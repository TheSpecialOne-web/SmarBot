import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Group, UpdateGroupParam } from "@/orval/models/backend-api";

type Props = {
  group: Group;
  onSubmit: (params: UpdateGroupParam) => void;
  onClose: () => void;
};

export const UpdateGroupForm = ({ group, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<UpdateGroupParam>({
    defaultValues: {
      name: group.name,
    },
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <CustomTextField
          control={control}
          rules={{ required: "グループ名は必須です" }}
          label="グループ名"
          autoFocus
          fullWidth
          name="name"
          type="text"
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
