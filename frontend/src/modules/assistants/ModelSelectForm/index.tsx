import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Button, FormControl, MenuItem, Select, Stack, Typography } from "@mui/material";
import { Control, FieldValues, Path, useController } from "react-hook-form";

import { CustomLabel } from "@/components/labels/CustomLabel";
import { modelNames } from "@/const/modelFamily";
import { useDisclosure } from "@/hooks/useDisclosure";
import { ModelFamily } from "@/orval/models/backend-api";

import { ModelDescriptionDialog } from "./ModelDescriptionDialog";

type Props<T extends FieldValues> = {
  control: Control<T>;
  modelFamilies: ModelFamily[];
};

export const ModelSelectForm = <T extends FieldValues>({ control, modelFamilies }: Props<T>) => {
  const {
    isOpen: isModelDescriptionDialogOpen,
    open: openModelDescriptionDialog,
    close: closeModelDescriptionDialog,
  } = useDisclosure({});

  const {
    field,
    fieldState: { error },
  } = useController<T>({
    name: "model_family" as Path<T>,
    control,
    rules: { required: "モデルを選択してください" },
  });

  const onSelect = (modelFamily: ModelFamily) => {
    field.onChange(modelFamily);
    closeModelDescriptionDialog();
  };

  return (
    <>
      <Stack gap={0.5}>
        <Stack direction="row" gap={1}>
          <CustomLabel label="モデル" required />
          <Button
            onClick={openModelDescriptionDialog}
            startIcon={<InfoOutlinedIcon sx={{ width: 16, height: 16 }} />}
            sx={{ py: 0.5, minWidth: "fit-content", "& .MuiButton-startIcon": { mr: 0.5 } }}
          >
            <Typography variant="caption">比較表</Typography>
          </Button>
        </Stack>
        <FormControl fullWidth error={Boolean(error)}>
          <Select {...field} fullWidth size="small">
            {modelFamilies.map(mf => (
              <MenuItem key={mf} value={mf}>
                {modelNames[mf]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>
      <ModelDescriptionDialog
        open={isModelDescriptionDialogOpen}
        onClose={closeModelDescriptionDialog}
        modelFamilies={modelFamilies}
        onSelect={onSelect}
      />
    </>
  );
};
