import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { FileInput } from "@/components/inputs/FileInput";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { createTenantGuideline } from "@/orval/backend-api";

type CreateTenantGuidelineFormParam = {
  file: File | null;
};

type Props = {
  onClose: () => void;
  refetch: () => void;
};

export const CreateTenantGuidelineForm = ({ onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const {
    userInfo: { tenant },
  } = useUserInfo();

  const {
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { isSubmitting },
  } = useForm<CreateTenantGuidelineFormParam>();
  const selectedFile = watch("file");

  const handleChangeFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValue("file", null);

    if (!event.target.files || event.target.files.length === 0) return;
    const file = Array.from(event.target.files).at(0);
    if (!file) return;
    setValue("file", file);
  };

  const onSubmit = async ({ file }: CreateTenantGuidelineFormParam) => {
    if (!file) return;

    try {
      await createTenantGuideline(tenant.id, { file });
      reset();
      setValue("file", null);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ガイドラインを作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ガイドラインの作成に失敗しました。" });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <CustomDialogContent>
        <FileInput file={selectedFile} onChange={handleChangeFile} allowedExtension="pdf" />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="送信" />
    </form>
  );
};
