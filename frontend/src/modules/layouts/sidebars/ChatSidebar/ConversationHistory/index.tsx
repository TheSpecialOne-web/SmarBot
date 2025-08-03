import { Box, List } from "@mui/material";
import { motion } from "framer-motion";

import { ListSkeletonLoading } from "@/components/loadings/ListSkeletonLoading";
import { Conversation } from "@/orval/models/backend-api";

import { SubtitleText } from "../SubtitleText";
import { ConversationItem } from "./Conversation";

type Props = {
  conversations: Conversation[];
  onCloseSidebar?: () => void;
  isLoadingFetchConversations?: boolean;
};

export const ConversationHistory = ({
  conversations,
  onCloseSidebar,
  isLoadingFetchConversations,
}: Props) => {
  // アイテム追加時の滑らかなアニメーションを定義
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <List>
      <SubtitleText text="会話履歴" />
      <Box overflow="auto">
        {isLoadingFetchConversations ? (
          <ListSkeletonLoading />
        ) : (
          conversations.map(conversation => (
            <motion.div
              layout
              initial="hidden"
              animate="show"
              variants={itemVariants}
              key={conversation.id}
            >
              <ConversationItem conversation={conversation} onCloseSidebar={onCloseSidebar} />
            </motion.div>
          ))
        )}
      </Box>
    </List>
  );
};
