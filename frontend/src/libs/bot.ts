import { Approach, Bot, BotStatus, PdfParser } from "@/orval/models/backend-api";
import { MODEL_COLORS } from "@/theme";

export const formatBotStatus = (status: BotStatus) => {
  switch (status) {
    case BotStatus.active:
      return "使用中";
    case BotStatus.archived:
      return "アーカイブ済み";
    case BotStatus.deleting:
      return "削除中";
    case BotStatus.basic_ai_deleted:
      return "削除済み（基盤モデル）";
  }
};

export const isAssistant = (bot: Bot) => {
  return ([Approach.neollm, Approach.custom_gpt, Approach.ursa] as string[]).includes(bot.approach);
};

export const isChatGptBot = (bot: Bot) => {
  return bot.approach === Approach.chat_gpt_default || bot.approach === Approach.text_2_image;
};

export const isUrsaBot = (bot: Bot) => {
  return bot.approach === Approach.ursa;
};

export const getBaseModelColor = (modelFamily: string) => {
  const baseModel = modelFamily.includes("dall-e") ? "gpt" : modelFamily.split("-")[0];

  return MODEL_COLORS[baseModel] || MODEL_COLORS.default;
};

export const getPdfParserLabel = (pdfParser: PdfParser) => {
  switch (pdfParser) {
    case PdfParser.pypdf:
      return "デフォルト";
    case PdfParser.ai_vision:
      return "OCR(光学文字認識)";
    case PdfParser.document_intelligence:
      return "OCR+表解析";
    case PdfParser.llm_document_reader:
      return "OCR+表/グラフ解析";
    default:
      return "デフォルト";
  }
};
