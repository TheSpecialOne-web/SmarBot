import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  conversationTitle: string;
  onArchive: () => Promise<void>;
  isArchiving: boolean;
};

export const DeleteConversationDialog = ({
  isOpen,
  onClose,
  conversationTitle,
  onArchive,
  isArchiving,
}: Props) => {
  return (
    <ConfirmDialog
      open={isOpen}
      onClose={onClose}
      title="会話の削除"
      content={
        <Typography>
          <Typography component="span" fontWeight="bold">
            {conversationTitle}
          </Typography>
          を削除しますか？
          <br />
          この操作は取り消せません。
        </Typography>
      }
      buttonText="削除"
      onSubmit={onArchive}
      isLoading={isArchiving}
    />
  );
};
