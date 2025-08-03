import {
  Attachment,
  ConversationPreview,
  ConversationResponse,
  DocumentFolder,
  Feedback,
} from "@/orval/models/backend-api";

export type ChatSession = {
  user: string;
  bot: ConversationResponse;
  attachments?: Attachment[];
  feedback?: Feedback;
  documentFolder?: DocumentFolder;
};

export type PreviewChatSession = {
  user: string;
  bot: ConversationPreview;
};
