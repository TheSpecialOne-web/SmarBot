import { InputAdornment, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import { Document, UpdateDocumentParam } from "@/orval/models/backend-api";

type Props = {
  document: Document;
  onSubmit: (params: UpdateDocumentParam) => void;
  onClose: () => void;
  isUrsaBot: boolean;
};

export const UpdateDocumentForm = ({ document, onSubmit, onClose, isUrsaBot }: Props) => {
  const { tmpUrsaPhase2 } = useFlags();
  const {
    control,
    handleSubmit,
    formState: { isSubmitting, isDirty },
  } = useForm<UpdateDocumentParam>({
    defaultValues: {
      basename: document.name,
      memo: document.memo,
    },
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        {tmpUrsaPhase2 ? (
          <CustomTextField
            control={control}
            label="名前"
            name="basename"
            autoFocus
            fullWidth
            type="text"
            InputProps={{
              endAdornment: (
                <InputAdornment position="start">{`.${document.file_extension}`}</InputAdornment>
              ),
            }}
            rules={{ required: "名前は必須です" }}
          />
        ) : (
          <Typography variant="h5">
            {document.name}.{document.file_extension}
          </Typography>
        )}
        <Spacer px={14} />
        <CustomTextField
          control={control}
          label="メモ"
          name="memo"
          autoFocus
          fullWidth
          type="text"
          disabled={isUrsaBot}
        />
      </CustomDialogContent>
      <CustomDialogAction
        onClose={onClose}
        buttonText="保存"
        loading={isSubmitting}
        disabled={!isDirty}
      />
    </form>
  );
};
