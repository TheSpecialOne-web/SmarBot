import json

from api.app import app
from api.infrastructures.postgres.models.bot import Bot
from api.infrastructures.postgres.models.document import Document


def main():
    with app.app_context():
        try:
            bots_with_documents = Bot.query.outerjoin(Document).all()
        except Exception as e:
            print(e)
            return

        container_documents = []
        for bot in bots_with_documents:
            if bot.approach == "chat_gpt_default":
                continue
            container_documents.append(
                {"container_name": bot.container_name, "basenames": [document.basename for document in bot.documents]}
            )

        # save container_documents to json file
        with open("./commands/container_documents.json", "w") as f:
            json.dump({"container_documents": container_documents}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
