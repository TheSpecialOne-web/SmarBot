import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CreateDocumentFolderParam, DocumentFolder } from "@/orval/models/backend-api";

type Props = {
  parentDocumentFolderId: DocumentFolder["id"] | null;
  onSubmit: (params: CreateDocumentFolderParam) => void;
  onClose: () => void;
};

export const CreateDocumentFolderForm = ({ parentDocumentFolderId, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateDocumentFolderParam>({
    defaultValues: {
      name: "",
      parent_document_folder_id: parentDocumentFolderId || undefined,
    },
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <CustomTextField
          control={control}
          rules={{ required: "フォルダ名を入力してください" }}
          label="フォルダ名"
          name="name"
          autoFocus
          fullWidth
          type="text"
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="追加" loading={isSubmitting} />
    </form>
  );
};
