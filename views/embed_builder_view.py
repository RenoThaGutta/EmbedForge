from __future__ import annotations

import datetime

import discord

from domain.embed_draft import EmbedDraft
from errors.app_errors import EmbedForgeError
from modals.advanced_modal import AdvancedModal
from modals.author_modal import AuthorModal
from modals.button_modal import ButtonModal
from modals.content_modal import ContentModal
from modals.fields_modal import FieldsModal
from modals.footer_modal import FooterModal
from modals.image_modal import ImageModal
from modals.template_name_modal import TemplateNameModal
from repositories.templates import list_embed_templates
from services.embed_renderer import build_preview_embed, has_text
from services.message_editor import send_draft_message, update_draft_message
from services.permissions import can_manage_embedforge
from services.plans import ensure_templates_enabled
from utils.logging import get_logger
from views.mention_views import MentionView
from views.template_views import TemplateManageView, TemplateSelectView

logger = get_logger("views.embed_builder_view")


class EmbedMakerView(discord.ui.View):
    def __init__(self, draft: EmbedDraft, author_id: int, templates_enabled: bool = True):
        super().__init__(timeout=600)
        self.draft = draft
        self.author_id = author_id
        self.message = None
        self.templates_enabled = templates_enabled

        try:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and getattr(child, "custom_id", None) == "update_this_message":
                    child.disabled = not bool(self.draft.edit_message_id)
                if (
                    isinstance(child, discord.ui.Button)
                    and getattr(child, "label", None) in {"Save Template", "Load Template", "Manage Templates"}
                ):
                    child.disabled = not self.templates_enabled
        except Exception:
            pass

        self.update_button_styles()

    def build_preview_content(self):
        try:
            content_parts = ["**Embed Maker** (Live Preview)"]

            if self.draft.loaded_template_name:
                content_parts.append(f"\U0001f4cb **Template:** {self.draft.loaded_template_name} (loaded)")

            if self.draft.edit_message_id:
                content_parts.append(
                    f"\U0001f6e0\ufe0f **Editing Message:** `{self.draft.edit_message_id}` (use **Update This Message**)"
                )

            if self.draft.mention_text:
                content_parts.append(f"\u2705 **Message Content:** {self.draft.mention_text}")
            else:
                content_parts.append("\u274c **Message Content:** None")

            if self.draft.title:
                content_parts.append(f"\u2705 **Title:** {self.draft.title}")
            else:
                content_parts.append("\u274c **Title:** Not set")

            if self.draft.message:
                preview_msg = self.draft.message[:100] + "..." if len(self.draft.message) > 100 else self.draft.message
                content_parts.append(f"\u2705 **Embed Text:** {preview_msg}")
            else:
                content_parts.append("\u274c **Embed Text:** Not set")

            image_status = []
            if self.draft.image_url:
                image_status.append("Main")
            if self.draft.thumbnail_url:
                image_status.append("Thumbnail")

            if image_status:
                content_parts.append(f"\u2705 **Images:** {', '.join(image_status)}")
            else:
                content_parts.append("\u274c **Images:** Not set")

            if has_text(self.draft.btn_label) and has_text(self.draft.btn_url):
                content_parts.append(
                    f"\u2705 **Button:** {self.draft.btn_label} -> "
                    f"{self.draft.btn_url[:50]}{'...' if len(self.draft.btn_url) > 50 else ''}"
                )
            else:
                content_parts.append("\u274c **Button:** Not set")

            if self.draft.author_name:
                content_parts.append(f"\u2705 **Author:** {self.draft.author_name}")
            else:
                content_parts.append("\u274c **Author:** Not set")

            if self.draft.footer_text:
                content_parts.append(
                    f"\u2705 **Footer:** {self.draft.footer_text[:30]}"
                    f"{'...' if len(self.draft.footer_text) > 30 else ''}"
                )
            else:
                content_parts.append("\u274c **Footer:** Not set")

            if self.draft.color_hex:
                content_parts.append(f"\u2705 **Color:** {self.draft.color_hex}")
            else:
                content_parts.append("\u274c **Color:** Default (Gold)")

            if self.draft.add_timestamp:
                content_parts.append("\u2705 **Timestamp:** Enabled")
            else:
                content_parts.append("\u274c **Timestamp:** Disabled")

            field_count = len(self.draft.fields) if self.draft.fields else 0
            if field_count > 0:
                field_names = [field["name"][:20] + ("..." if len(field["name"]) > 20 else "") for field in self.draft.fields[:3]]
                content_parts.append(
                    f"\u2705 **Fields:** {field_count} field{'s' if field_count != 1 else ''} ({', '.join(field_names)})"
                )
            else:
                content_parts.append("\u274c **Fields:** Not set")

            content_parts.append("\n*Use the buttons below to edit your embed:*")
            return "\n".join(content_parts)
        except Exception as exc:
            logger.exception("Error building preview content")
            return "**Embed Maker** (Error loading preview - but buttons should still work)"

    async def update_preview_direct(self):
        if self.message:
            try:
                content = self.build_preview_content()
                preview_embed = build_preview_embed(self.draft)
                self.update_button_styles()

                kwargs = {"content": content, "view": self}
                if preview_embed:
                    kwargs["embed"] = preview_embed

                await self.message.edit(**kwargs)
            except discord.NotFound:
                logger.warning("Message not found while updating preview")
                self.message = None
            except discord.HTTPException as exc:
                if "Unknown interaction" in str(exc):
                    logger.warning("Interaction expired while updating preview")
                    self.message = None
                else:
                    logger.warning("HTTP error updating preview: %s", exc)
            except Exception as exc:
                logger.exception("Failed to update preview")
        else:
            logger.debug("No message reference available for preview update")

    async def update_preview(self, interaction: discord.Interaction):
        await self.update_preview_direct()

    async def on_timeout(self):
        try:
            for child in self.children:
                child.disabled = True

            if self.message:
                await self.message.edit(
                    content="\u23f0 Builder timed out after 10 minutes. Use `/embed_maker` to create a new one.",
                    view=self,
                )
        except Exception as exc:
            logger.exception("Error in on_timeout")

    def update_button_styles(self):
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This embed maker belongs to someone else. Use `/embed_maker` to create your own!",
                ephemeral=True,
                delete_after=5,
            )
            return False
        return True

    @discord.ui.button(label="Edit Content", style=discord.ButtonStyle.secondary, row=0)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContentModal(self.draft))

    @discord.ui.button(label="Set Images", style=discord.ButtonStyle.secondary, row=0)
    async def set_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ImageModal(self.draft))

    @discord.ui.button(label="Set Mention", style=discord.ButtonStyle.secondary, row=0)
    async def set_mention(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("\u274c This command can only be used in a server.", ephemeral=True, delete_after=5)
            return

        view = MentionView(self.draft, interaction.guild)
        await interaction.response.send_message("Choose who to mention:", view=view, ephemeral=True, delete_after=30)

    @discord.ui.button(label="Add Button", style=discord.ButtonStyle.secondary, row=0)
    async def set_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ButtonModal(self.draft))

    @discord.ui.button(label="Set Author", style=discord.ButtonStyle.secondary, row=1)
    async def set_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AuthorModal(self.draft))

    @discord.ui.button(label="Set Footer", style=discord.ButtonStyle.secondary, row=1)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FooterModal(self.draft))

    @discord.ui.button(label="Set Color", style=discord.ButtonStyle.secondary, row=1)
    async def set_advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdvancedModal(self.draft))

    @discord.ui.button(label="Edit Fields", style=discord.ButtonStyle.secondary, row=1)
    async def set_fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FieldsModal(self.draft))

    @discord.ui.button(label="Save Template", style=discord.ButtonStyle.secondary, row=2)
    async def save_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("\u274c Templates can only be saved in servers.", ephemeral=True, delete_after=5)
            return
        try:
            await ensure_templates_enabled(interaction.client, interaction.guild.id)
        except EmbedForgeError as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return
        await interaction.response.send_modal(TemplateNameModal(self.draft, interaction.guild.id))

    @discord.ui.button(label="Load Template", style=discord.ButtonStyle.secondary, row=2)
    async def load_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("\u274c Templates can only be loaded in servers.", ephemeral=True, delete_after=5)
            return
        try:
            await ensure_templates_enabled(interaction.client, interaction.guild.id)
        except EmbedForgeError as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return

        templates = list_embed_templates(interaction.guild.id)
        if not templates:
            await interaction.response.send_message(
                "\u274c No templates saved for this server yet. Create one with the 'Save Template' button!",
                ephemeral=True,
                delete_after=5,
            )
            return

        template_view = TemplateSelectView(self.draft, self, interaction.guild.id, templates)
        await interaction.response.send_message("\U0001f4cb **Select a template to load:**", view=template_view, ephemeral=True, delete_after=60)

    @discord.ui.button(label="Manage Templates", style=discord.ButtonStyle.secondary, row=2)
    async def manage_templates(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("\u274c Templates can only be managed in servers.", ephemeral=True, delete_after=5)
            return
        try:
            await ensure_templates_enabled(interaction.client, interaction.guild.id)
        except EmbedForgeError as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return

        templates = list_embed_templates(interaction.guild.id)
        if not templates:
            await interaction.response.send_message(
                "\u274c No templates saved for this server yet. Create one with the 'Save Template' button first!",
                ephemeral=True,
                delete_after=5,
            )
            return

        manage_view = TemplateManageView(interaction.guild.id, templates)
        await interaction.response.send_message(
            "\U0001f6e0\ufe0f **Template Management**\nSelect a template to delete or update:",
            view=manage_view,
            ephemeral=True,
            delete_after=60,
        )

    @discord.ui.button(label="Toggle Time", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_timestamp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.draft.add_timestamp = not self.draft.add_timestamp
        status = "enabled" if self.draft.add_timestamp else "disabled"
        await interaction.response.send_message(f"\u23f0 Timestamp {status}.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass

    @discord.ui.button(label="Test Preview", style=discord.ButtonStyle.secondary, row=3)
    async def test_preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.draft.build_embed()
        view = self.draft.build_view()

        body = None if embed else (self.draft.message or "*No message*")
        if self.draft.mention_text:
            body = (body or "") + ("\n" if body else "") + f"**Message content:** {self.draft.mention_text}"

        header = "**Test Preview** (exactly how it will look when sent)"
        content = header if body is None else f"{header}\n{body}"

        kwargs = {"content": content, "ephemeral": True, "delete_after": 15}
        if embed is not None:
            kwargs["embed"] = embed
        if view is not None:
            kwargs["view"] = view
        await interaction.response.send_message(**kwargs)

    @discord.ui.button(label="Update This Message", style=discord.ButtonStyle.primary, row=4, custom_id="update_this_message")
    async def update_this_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await can_manage_embedforge(interaction):
            return await interaction.response.send_message(
                "You need **Manage Server** permissions to update messages.",
                ephemeral=True,
                delete_after=5,
            )

        if not self.draft.edit_channel_id or not self.draft.edit_message_id:
            return await interaction.response.send_message(
                "\u274c No edit target set for this builder.",
                ephemeral=True,
                delete_after=5,
            )

        await interaction.response.defer(ephemeral=True)

        try:
            await update_draft_message(interaction, self.draft)
            await interaction.followup.send("\u2705 Message updated.", ephemeral=True)
        except EmbedForgeError as exc:
            await interaction.followup.send(f"\u274c {exc}", ephemeral=True)
        except Exception as exc:
            logger.exception("Unexpected error updating target message")
            await interaction.followup.send(
                f"\u274c Update failed: `{exc.__class__.__name__}: {str(exc)}`",
                ephemeral=True,
            )

    @discord.ui.button(label="Send Here", style=discord.ButtonStyle.success, row=4)
    async def send_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await can_manage_embedforge(interaction):
            return await interaction.response.send_message(
                "You need **Manage Server** permissions to send.",
                ephemeral=True,
                delete_after=5,
            )

        if not (has_text(self.draft.message) or has_text(self.draft.title) or has_text(self.draft.image_url)):
            return await interaction.response.send_message(
                "Add a message or a title/image before sending.",
                ephemeral=True,
                delete_after=5,
            )

        channel = interaction.channel
        if channel is None:
            return await interaction.response.send_message("\u274c No channel context.", ephemeral=True, delete_after=5)

        await interaction.response.defer(ephemeral=True)

        try:
            await send_draft_message(interaction, self.draft)
        except EmbedForgeError as exc:
            return await interaction.followup.send(f"\u274c {exc}", ephemeral=True)
        except Exception as exc:
            return await interaction.followup.send(
                f"\u274c Send failed: `{exc.__class__.__name__}: {str(exc)}`",
                ephemeral=True,
            )

        for child in self.children:
            child.disabled = True

        try:
            await interaction.followup.edit_message(
                interaction.message.id,
                content="\u2705 Embed sent successfully! Closing in 2 seconds...",
                view=self,
            )
        except Exception:
            await interaction.followup.send("\u2705 Embed sent successfully!", ephemeral=True)

        try:
            await discord.utils.sleep_until(datetime.datetime.now().astimezone() + datetime.timedelta(seconds=2))
            await interaction.delete_original_response()
        except Exception:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(content="\u274c Builder cancelled. Closing...", view=self)

        try:
            await discord.utils.sleep_until(datetime.datetime.now().astimezone() + datetime.timedelta(seconds=1))
            await interaction.delete_original_response()
        except Exception:
            pass

