import { ListItem, ListItemButton, Stack } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";

import { useConversation } from "@/hooks/useConversation";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useScreen } from "@/hooks/useScreen";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { useUpdateConversation } from "@/orval/backend-api";
import { Conversation, UpdateConversationParam } from "@/orval/models/backend-api";

import { ConversationActionButton } from "./ConversationActionButton";
import { ConversationTitle } from "./ConversationTitle";
import { DeleteConversationDialog } from "./DeleteConversationDialog";

type Props = {
  conversation: Conversation;
  onCloseSidebar?: () => void;
};

type FormValues = {
  title: string;
};

export const ConversationItem = ({ conversation, onCloseSidebar }: Props) => {
  const { userInfo } = useUserInfo();
  const { updateTitle, refreshConversations } = useConversation();
  const { isTablet } = useScreen();
  const { control, reset } = useForm<FormValues>({
    defaultValues: {
      title: conversation.title,
    },
  });
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const [isEditing, setIsEditing] = useState(false);
  const {
    isOpen: isDeleteDialogOpen,
    open: openDeleteDialog,
    close: closeDeleteDialog,
  } = useDisclosure({});

  const urlParams = useParams<{ conversationId: string }>();
  const isCurrent = urlParams.conversationId === conversation.id;

  const navigate = useNavigate();

  const { trigger: archiveConversation, isMutating: isArchiving } = useUpdateConversation(
    userInfo.id,
    conversation.id,
  );

  const onArchive = async () => {
    try {
      const updateParam: UpdateConversationParam = {
        is_archived: true,
      };
      await archiveConversation(updateParam);
      if (isCurrent) {
        navigate("/main/chat");
      }
      refreshConversations();
      closeDeleteDialog();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "会話の削除に失敗しました。" });
    }
  };

  const onSubmit = async (data: FormValues) => {
    try {
      await updateTitle(conversation.id, data.title);
      reset({ title: data.title });
      setIsEditing(false);
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "タイトルの変更に失敗しました。" });
    }
  };

  return (
    <>
      <ListItem sx={{ p: 0 }} title={conversation.title}>
        <ListItemButton
          sx={{
            px: 1,
            py: 0.75,
            fontSize: "14px",
            fontWeight: 500,
            bgcolor: isCurrent ? grey[200] : "transparent",
            borderRadius: 2,
          }}
          disableRipple
          onClick={() => {
            if (isTablet) {
              onCloseSidebar?.();
            }
            navigate(`/main/chat/${conversation.id}?botId=${conversation.bot_id}`);
          }}
          onDoubleClick={e => {
            if (isEditing) return;
            if (!isCurrent) return;
            e.preventDefault();
            setIsEditing(true);
          }}
        >
          <Stack direction="row" alignItems="center" justifyContent="space-between" width="100%">
            <ConversationTitle
              isEditing={isEditing}
              title={conversation.title}
              control={control}
              onSubmit={onSubmit}
            />
            <ConversationActionButton
              onChangeTitle={() => {
                navigate(`/main/chat/${conversation.id}?botId=${conversation.bot_id}`);
                setIsEditing(true);
              }}
              onDelete={openDeleteDialog}
            />
          </Stack>
        </ListItemButton>
      </ListItem>
      <DeleteConversationDialog
        isOpen={isDeleteDialogOpen}
        onClose={closeDeleteDialog}
        conversationTitle={conversation.title}
        onArchive={onArchive}
        isArchiving={isArchiving}
      />
    </>
  );
};
