import { DeleteOutlineOutlined } from "@mui/icons-material";
import AddIcon from "@mui/icons-material/Add";
import { Divider, Grid, IconButton, Stack } from "@mui/material";
import { useFieldArray, useForm } from "react-hook-form";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { Spacer } from "@/components/spacers/Spacer";
import { TermV2, UpdateTermParamV2 } from "@/orval/models/backend-api";

type Props = {
  term?: TermV2;
  onSubmit: (param: UpdateTermParamV2) => Promise<void>;
  onClose: () => void;
};

type TermFormParam = {
  names: { name: string }[];
  description: string;
};

export const CreateOrUpdateTermForm = ({ term, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<TermFormParam>({
    defaultValues: {
      names: term?.names?.map(name => ({ name })) || [{ name: "" }],
      description: term?.description || "",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "names",
  });

  const addNameField = () => {
    append({ name: "" });
  };

  const handleFormSubmit = async (data: TermFormParam) => {
    const updatedData: UpdateTermParamV2 = {
      description: data.description,
      names: data.names.filter(field => field.name.trim() !== "").map(field => field.name),
    };
    await onSubmit(updatedData);
  };

  return (
    <form noValidate onSubmit={handleSubmit(handleFormSubmit)}>
      <CustomDialogContent>
        <Grid container justifyContent="space-around" spacing={2}>
          <Grid item xs={5}>
            <CustomLabel label="用語" required />
            <Stack spacing={1}>
              {fields.map((field, index) => (
                <Stack key={field.id} direction="row" spacing={1}>
                  <CustomTextField
                    name={`names.${index}.name`}
                    fullWidth
                    variant="outlined"
                    control={control}
                    rules={{ required: "用語は必須です" }}
                    boxSx={{ flexGrow: 1 }}
                  />
                  <IconButton
                    onClick={() => remove(index)}
                    color="error"
                    disabled={fields.length === 1}
                  >
                    <DeleteOutlineOutlined />
                  </IconButton>
                </Stack>
              ))}
            </Stack>
            <Spacer px={16} />
            <PrimaryButton
              text="用語を追加"
              variant="outlined"
              onClick={addNameField}
              startIcon={<AddIcon />}
              loading={isSubmitting}
            />
          </Grid>

          <Grid item sx={{ alignSelf: "stretch" }}>
            <Divider orientation="vertical" />
          </Grid>

          <Grid item xs={6}>
            <CustomTextField
              name="description"
              label="説明"
              fullWidth
              variant="outlined"
              multiline
              rows={12}
              control={control}
              rules={{ required: "説明は必須です" }}
            />
          </Grid>
        </Grid>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="保存" />
    </form>
  );
};
