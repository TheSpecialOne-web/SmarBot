import { Stack } from "@mui/material";
import { useForm } from "react-hook-form";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Tenant, UpdateTenantParam } from "@/orval/models/administrator-api";
import { bytesToGb, gbToBytes } from "@/utils/formatBytes";

type Props = {
  tenant: Tenant;
  handleUpdateTenant: (params: UpdateTenantParam) => Promise<void>;
};

export const UsageLimitForm = ({ tenant, handleUpdateTenant }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<Tenant["usage_limit"]>({
    defaultValues: {
      ...tenant.usage_limit,
      free_storage: bytesToGb(tenant.usage_limit.free_storage),
      additional_storage: bytesToGb(tenant.usage_limit.additional_storage),
    },
  });

  const handleFormSubmit = async ({
    free_user_seat,
    additional_user_seat,
    free_token,
    additional_token,
    free_storage,
    additional_storage,
    document_intelligence_page,
  }: Tenant["usage_limit"]) => {
    await handleUpdateTenant({
      ...tenant,
      usage_limit: {
        free_user_seat: Number(free_user_seat),
        additional_user_seat: Number(additional_user_seat),
        free_token: Number(free_token),
        additional_token: Number(additional_token),
        free_storage: gbToBytes(Number(free_storage)),
        additional_storage: gbToBytes(Number(additional_storage)),
        document_intelligence_page: Number(document_intelligence_page),
      },
    });
  };

  const handleWheel = (event: React.WheelEvent<HTMLInputElement>) => {
    event.currentTarget.blur();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <Stack gap={2}>
        <CustomTextField
          fullWidth
          control={control}
          name="free_user_seat"
          type="number"
          label="無料ユーザー数"
          rules={{
            required: "必須項目です",
            min: { value: 0, message: "0 以上の数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="additional_user_seat"
          type="number"
          label="追加ユーザー数"
          rules={{
            required: "必須項目です",
            min: { value: 0, message: "0 以上の数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="free_token"
          type="number"
          label="無料トークン数"
          rules={{
            required: "必須項目です",
            min: { value: 1, message: "0より大きい数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="additional_token"
          type="number"
          label="追加トークン数"
          rules={{
            required: "必須項目です",
            min: { value: 0, message: "0 以上の数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="free_storage"
          type="number"
          label="無料ストレージ容量（GB）"
          rules={{
            required: "必須項目です",
            min: { value: 1, message: "0より大きい数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="additional_storage"
          type="number"
          label="追加ストレージ容量（GB）"
          rules={{
            required: "必須項目です",
            min: { value: 0, message: "0 以上の数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <CustomTextField
          fullWidth
          control={control}
          name="document_intelligence_page"
          type="number"
          label="高精度表読み取り+OCR処理数"
          rules={{
            required: "必須項目です",
            min: { value: 0, message: "0 以上の数値を入力してください。" },
          }}
          inputProps={{
            onWheel: handleWheel,
          }}
        />
        <PrimaryButton text="保存" type="submit" loading={isSubmitting} />
      </Stack>
    </form>
  );
};
