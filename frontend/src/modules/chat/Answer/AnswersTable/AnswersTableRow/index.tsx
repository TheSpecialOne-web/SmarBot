import ThumbUpAltIcon from "@mui/icons-material/ThumbUpAlt";
import ThumbUpOffAltIcon from "@mui/icons-material/ThumbUpOffAlt";
import { Box, Chip, Link, Stack, TableCell, TableRow, Tooltip } from "@mui/material";
import { blue } from "@mui/material/colors";

import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { updateDocumentFeedback } from "@/orval/backend-api";
import { Bot, DataPoint, DocumentFeedbackSummary } from "@/orval/models/backend-api";

type Props = {
  botId: Bot["id"];
  dataPoint: DataPoint;
  additionalInfoKeys: string[];
  documentIdToDocumentFeedbackMap: Map<number, DocumentFeedbackSummary>;
  onClickCitation: (citation: DataPoint) => void;
  refetchDataPoints: () => void;
};

const goodEvaluationCss = {
  borderColor: "primary.main",
  color: "primary.main",
  bgcolor: blue[50],
};

export const AnswersTableRow = ({
  botId,
  dataPoint,
  additionalInfoKeys,
  documentIdToDocumentFeedbackMap,
  onClickCitation,
  refetchDataPoints,
}: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const feedback = dataPoint.document_id
    ? documentIdToDocumentFeedbackMap.get(dataPoint.document_id)
    : undefined;

  const updateFeedback = async () => {
    if (!botId) return;
    if (!dataPoint.document_id) {
      enqueueErrorSnackbar({
        message: "ドキュメントが存在しません。",
      });
      return;
    }
    try {
      await updateDocumentFeedback(botId, dataPoint.document_id, {
        evaluation: feedback?.user_evaluation === "good" ? null : "good",
      });
      refetchDataPoints();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "フィードバックの更新に失敗しました。",
      });
    }
  };

  return (
    <TableRow key={dataPoint.cite_number}>
      <TableCell sx={{ minWidth: 200 }}>
        <Stack gap={1}>
          <Link
            onClick={() => onClickCitation(dataPoint)}
            sx={{
              cursor: "pointer",
            }}
          >
            {dataPoint.chunk_name}
          </Link>
          <Box position="relative" height={24}>
            <Tooltip title="良いドキュメント" placement={"bottom"} arrow>
              <Chip
                icon={
                  feedback?.user_evaluation === "good" ? (
                    <ThumbUpAltIcon color="primary" />
                  ) : (
                    <ThumbUpOffAltIcon />
                  )
                }
                label={feedback?.total_good ?? 0}
                variant="outlined"
                onClick={updateFeedback}
                size="small"
                sx={{
                  position: "absolute",
                  right: 0,
                  pl: 0.5,
                  "&&:hover": {
                    bgcolor: blue[50],
                  },
                  ...(feedback?.user_evaluation === "good" && goodEvaluationCss),
                }}
              />
            </Tooltip>
          </Box>
        </Stack>
      </TableCell>
      {additionalInfoKeys.map(key => (
        <TableCell key={key}>
          {dataPoint?.additional_info ? dataPoint.additional_info[key] : ""}
        </TableCell>
      ))}
    </TableRow>
  );
};
