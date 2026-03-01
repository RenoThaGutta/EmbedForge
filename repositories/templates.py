from __future__ import annotations

import json
import shutil
from typing import Optional

from config import TEMPLATE_BACKUP_FILE, TEMPLATE_FILE
from domain.embed_draft import EmbedDraft
from utils.logging import get_logger

logger = get_logger("repositories.templates")


class JsonTemplateRepository:
    def __init__(self, template_file=TEMPLATE_FILE, backup_file=TEMPLATE_BACKUP_FILE):
        self.template_file = template_file
        self.backup_file = backup_file

    def save_template(self, name: str, draft: EmbedDraft, guild_id: int) -> None:
        data = {
            "mention_text": draft.mention_text,
            "title": draft.title,
            "message": draft.message,
            "image_url": draft.image_url,
            "btn_label": draft.btn_label,
            "btn_url": draft.btn_url,
            "footer_text": draft.footer_text,
            "footer_icon_url": draft.footer_icon_url,
            "thumbnail_url": draft.thumbnail_url,
            "author_name": draft.author_name,
            "author_icon_url": draft.author_icon_url,
            "author_url": draft.author_url,
            "color_hex": draft.color_hex,
            "add_timestamp": draft.add_timestamp,
            "fields": draft.fields,
        }

        all_templates = self._load_all_templates()
        guild_templates = all_templates.get(str(guild_id), {})
        guild_templates[name] = data
        all_templates[str(guild_id)] = guild_templates
        self._write_all_templates(all_templates)

    def load_template(self, name: str, guild_id: int) -> Optional[dict]:
        all_templates = self._load_all_templates()
        guild_templates = all_templates.get(str(guild_id), {})
        return guild_templates.get(name)

    def list_templates(self, guild_id: int) -> list:
        all_templates = self._load_all_templates()
        guild_templates = all_templates.get(str(guild_id), {})
        return list(guild_templates.keys())

    def delete_template(self, name: str, guild_id: int) -> bool:
        try:
            all_templates = self._load_all_templates()
            guild_templates = all_templates.get(str(guild_id), {})
            if name not in guild_templates:
                return False

            del guild_templates[name]
            all_templates[str(guild_id)] = guild_templates
            self._write_all_templates(all_templates)
            return True
        except Exception:
            logger.exception("Error deleting template")
            return False

    def get_template_info(self, name: str, guild_id: int) -> Optional[dict]:
        try:
            template_data = self.load_template(name, guild_id)
            if not template_data:
                return None

            content_parts = []
            if template_data.get("title"):
                content_parts.append("Title")
            if template_data.get("message"):
                content_parts.append("Message")
            if template_data.get("image_url"):
                content_parts.append("Image")
            if template_data.get("btn_label") and template_data.get("btn_url"):
                content_parts.append("Button")
            if template_data.get("footer_text"):
                content_parts.append("Footer")
            if template_data.get("author_name"):
                content_parts.append("Author")
            if template_data.get("thumbnail_url"):
                content_parts.append("Thumbnail")
            if template_data.get("fields"):
                content_parts.append(f"{len(template_data['fields'])} Fields")

            return {
                "name": name,
                "content_parts": content_parts,
                "content_summary": ", ".join(content_parts) if content_parts else "Empty template",
            }
        except Exception:
            logger.exception("Error getting template info")
            return None

    def _load_all_templates(self) -> dict:
        if not self.template_file.exists():
            return {}

        try:
            with self.template_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError:
            logger.exception("Template store is invalid JSON; attempting backup recovery")
            return self._load_backup_templates()
        except Exception:
            logger.exception("Failed reading template store")
            return self._load_backup_templates()

        if not isinstance(data, dict):
            logger.warning("Template store root was not an object; ignoring invalid contents")
            return {}

        return data

    def _load_backup_templates(self) -> dict:
        if not self.backup_file.exists():
            return {}

        try:
            with self.backup_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            logger.exception("Failed reading template backup store")
            return {}

        if isinstance(data, dict):
            return data

        logger.warning("Template backup store root was not an object; ignoring invalid contents")
        return {}

    def _write_all_templates(self, data: dict) -> None:
        self.template_file.parent.mkdir(parents=True, exist_ok=True)

        if self.template_file.exists():
            try:
                shutil.copy2(self.template_file, self.backup_file)
            except Exception:
                logger.exception("Failed to refresh template backup before write")

        temp_file = self.template_file.with_suffix(self.template_file.suffix + ".tmp")
        with temp_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.flush()

        temp_file.replace(self.template_file)


repository = JsonTemplateRepository()


def save_embed_template(name: str, draft: EmbedDraft, guild_id: int) -> None:
    repository.save_template(name, draft, guild_id)


def load_embed_template(name: str, guild_id: int) -> Optional[dict]:
    return repository.load_template(name, guild_id)


def list_embed_templates(guild_id: int) -> list:
    return repository.list_templates(guild_id)


def delete_embed_template(name: str, guild_id: int) -> bool:
    return repository.delete_template(name, guild_id)


def get_template_info(name: str, guild_id: int) -> Optional[dict]:
    return repository.get_template_info(name, guild_id)

