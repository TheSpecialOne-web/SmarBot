import { DeleteOutlineOutlined } from "@mui/icons-material";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { Box, IconButton, Stack, Typography } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { QuestionAnswer, QuestionAnswerStatus } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

const filterQuestionAnswer = (question_answers: QuestionAnswer[], query: string) => {
  return question_answers.filter(questionAnswer => {
    return filterTest(query, [questionAnswer.question, questionAnswer.answer]);
  });
};

const sortQuestionAnswers = (
  questionAnswers: QuestionAnswer[],
  order: Order,
  orderBy: keyof QuestionAnswer,
) => {
  const comparator = getComparator<QuestionAnswer>(order, orderBy);
  return [...questionAnswers].sort(comparator);
};

const displayQuestionAnswerStatus = (status: QuestionAnswerStatus) => {
  switch (status) {
    case QuestionAnswerStatus.pending:
      return "処理中";
    case QuestionAnswerStatus.overwriting:
      return "更新中";
    case QuestionAnswerStatus.indexed:
      return "反映済み";
    case QuestionAnswerStatus.failed:
      return "エラー";
  }
};

const tableColumns: CustomTableColumn<QuestionAnswer>[] = [
  {
    key: "question",
    label: "質問",
    align: "left",
    sortFunction: sortQuestionAnswers,
  },
  {
    key: "answer",
    label: "回答",
    align: "left",
    sortFunction: sortQuestionAnswers,
  },
  {
    key: "updated_at",
    label: "最終更新日時",
    align: "left",
    sortFunction: sortQuestionAnswers,
    render: (questionAnswer: QuestionAnswer) => {
      return formatDate(questionAnswer.updated_at);
    },
  },
  {
    key: "status",
    label: "ステータス",
    align: "left",
    render: row => {
      return displayQuestionAnswerStatus(row.status);
    },
    columnFilterProps: {
      filterItems: Object.values(QuestionAnswerStatus).map(status => ({
        key: status,
        label: displayQuestionAnswerStatus(status),
      })),
      filterFunction: (questionAnswers: QuestionAnswer[], queries: string[]) => {
        return questionAnswers.filter(questionAnswer => queries.includes(questionAnswer.status));
      },
    },
  },
];

type Props = {
  questionAnswers: QuestionAnswer[];
  hasWritePolicy: boolean;
  onClickUpdateIcon: (questionAnswer: QuestionAnswer) => void;
  onClickDeleteIcon: (questionAnswer: QuestionAnswer) => void;
};

const noQuestionAnswerContent = (
  <Box
    sx={{
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
    }}
  >
    <Typography variant="body2">
      右上の「追加」ボタンをクリックしてFAQを追加してください。
    </Typography>
  </Box>
);

export const QuestionAnswersTable = ({
  questionAnswers,
  hasWritePolicy,
  onClickUpdateIcon,
  onClickDeleteIcon,
}: Props) => {
  const renderActionColumn = (qa: QuestionAnswer) => {
    const buttonDisabled =
      qa.status === QuestionAnswerStatus.pending || qa.status === QuestionAnswerStatus.overwriting;
    if (!hasWritePolicy) return null;
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton onClick={() => onClickUpdateIcon(qa)} color="primary" disabled={buttonDisabled}>
          <EditOutlinedIcon />
        </IconButton>
        <IconButton onClick={() => onClickDeleteIcon(qa)} color="error" disabled={buttonDisabled}>
          <DeleteOutlineOutlined />
        </IconButton>
      </Stack>
    );
  };

  return (
    <CustomTable<QuestionAnswer>
      tableColumns={tableColumns}
      tableData={questionAnswers}
      noDataContent={noQuestionAnswerContent}
      searchFilter={filterQuestionAnswer}
      defaultSortProps={{ key: "updated_at", order: "desc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
