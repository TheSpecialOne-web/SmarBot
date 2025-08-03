import { Box, Stack, Typography } from "@mui/material";

import { ResizableDrawer } from "@/components/drawers/ResizableDrawer";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { GuidelineDetail } from "@/orval/models/backend-api";

const TITLE_STACK_HEIGHT = "55px";

type Props = {
  open: boolean;
  onClose: () => void;
  guidelineDetail: GuidelineDetail;
  loading: boolean;
  error: boolean;
};

export const PreviewTenantGuidelineDrawer = ({
  open,
  onClose,
  guidelineDetail,
  loading,
  error,
}: Props) => (
  <ResizableDrawer open={open} onClose={onClose}>
    {loading ? (
      <Stack height="100%" justifyContent="center" alignItems="center">
        <CircularLoading />
      </Stack>
    ) : error ? (
      <Typography
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
        }}
        variant="h4"
      >
        ガイドラインの読み込みに失敗しました。
      </Typography>
    ) : (
      <Box height="100%" overflow="hidden">
        <Box height={`calc(100% - ${TITLE_STACK_HEIGHT})`}>
          <Stack px={2} height={TITLE_STACK_HEIGHT}>
            <Typography variant="h6" py={2}>
              {guidelineDetail.filename}
            </Typography>
          </Stack>
          <iframe title="Citation" src={guidelineDetail.signed_url} width="100%" height="100%" />
        </Box>
      </Box>
    )}
  </ResizableDrawer>
);
