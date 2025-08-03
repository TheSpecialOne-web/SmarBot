import { Bot } from "@/orval/models/backend-api";

export type BotWithLikedStatus = Bot & { isLiked: boolean };
