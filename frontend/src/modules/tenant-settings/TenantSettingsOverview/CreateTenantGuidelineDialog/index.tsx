import { CustomDialog } from "@/components/dialogs/CustomDialog";

import { CreateTenantGuidelineForm } from "./CreateTenantGuidelineForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateTenantGuidelineDialog = ({ open, onClose, refetch }: Props) => {
  return (
    <CustomDialog open={open} title="ガイドライン作成">
      <CreateTenantGuidelineForm onClose={onClose} refetch={refetch} />
    </CustomDialog>
  );
};
