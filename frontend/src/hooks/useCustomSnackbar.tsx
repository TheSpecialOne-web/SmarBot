import { SnackbarKey, useSnackbar } from "notistack";

import { SnackbarLoading } from "@/components/loadings/SnackbarLoading";

export const useCustomSnackbar = () => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();

  const enqueueErrorSnackbar = ({
    message,
    preventDuplicate = true,
  }: {
    message: string;
    preventDuplicate?: boolean;
  }) =>
    enqueueSnackbar(message, {
      variant: "error",
      preventDuplicate,
    });

  const enqueueSuccessSnackbar = ({
    message,
    preventDuplicate = true,
  }: {
    message: string;
    preventDuplicate?: boolean;
  }) =>
    enqueueSnackbar(message, {
      variant: "success",
      preventDuplicate,
    });

  const enqueueLoadingSnackbar = ({
    message,
    preventDuplicate = true,
  }: {
    message: string;
    preventDuplicate?: boolean;
  }) =>
    enqueueSnackbar(<SnackbarLoading message={message} />, {
      variant: "default",
      preventDuplicate,
    });

  const closeEnqueuedSnackbar = (snackbarId: SnackbarKey) => closeSnackbar(snackbarId);

  return {
    enqueueErrorSnackbar,
    enqueueSuccessSnackbar,
    enqueueLoadingSnackbar,
    closeEnqueuedSnackbar,
  };
};
