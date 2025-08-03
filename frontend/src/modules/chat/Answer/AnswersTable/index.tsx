import {
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { useState } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { DataPoint } from "@/orval/models/backend-api";
import { Bot, DocumentFeedbackSummary } from "@/orval/models/backend-api";

import { AnswersTableRow } from "./AnswersTableRow";

type Props = {
  botId: Bot["id"];
  dataPoints: DataPoint[];
  documentIdToDocumentFeedbackMap: Map<number, DocumentFeedbackSummary>;
  onClickCitation: (citation: DataPoint) => void;
  refetchDataPoints: () => void;
};

const getAdditionalInfoKeys = (dataPoints: DataPoint[]): string[] => {
  const additionalInfoKeys = dataPoints.flatMap(dataPoint => {
    if (!dataPoint.additional_info) return [];
    return Object.keys(dataPoint.additional_info);
  });
  return Array.from(new Set(additionalInfoKeys));
};

export const AnswersTable = ({
  botId,
  dataPoints,
  documentIdToDocumentFeedbackMap,
  onClickCitation,
  refetchDataPoints,
}: Props) => {
  const additionalInfoKeys = getAdditionalInfoKeys(dataPoints);
  const [page, setPage] = useState(1); // ページ番号を1から始める
  const itemsPerPage = 5;

  const paginatedDataPoints = dataPoints.slice(
    (page - 1) * itemsPerPage, // ページ番号を0ベースのインデックスに変換
    page * itemsPerPage,
  );
  const pageCount = Math.ceil(dataPoints.length / itemsPerPage);

  const onChangePage = (newPage: number) => {
    setPage(newPage); // ここで受け取ったページ番号をそのまま設定
  };

  return (
    <TableContainer sx={{ maxWidth: "100%", overflowX: "auto" }}>
      <Table
        sx={{
          border: 1,
          borderColor: "drawerBackground.main",
        }}
      >
        <TableHead
          sx={{
            backgroundColor: "onHover.main",
          }}
        >
          <TableRow>
            <TableCell
              sx={{
                fontWeight: "bold",
                whiteSpace: "nowrap",
              }}
            >
              ファイル名
            </TableCell>
            {additionalInfoKeys.map(key => (
              <TableCell
                key={key}
                sx={{
                  fontWeight: "bold",
                  whiteSpace: "nowrap",
                }}
              >
                {key}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {paginatedDataPoints.map(dataPoint => (
            <AnswersTableRow
              key={dataPoint.cite_number}
              botId={botId}
              dataPoint={dataPoint}
              additionalInfoKeys={additionalInfoKeys}
              documentIdToDocumentFeedbackMap={documentIdToDocumentFeedbackMap}
              onClickCitation={onClickCitation}
              refetchDataPoints={refetchDataPoints}
            />
          ))}
        </TableBody>
      </Table>
      <Spacer px={8} />
      <Pagination
        count={pageCount}
        onChange={(_, newPage) => onChangePage(newPage)}
        page={page}
        size="small"
        sx={{
          display: "flex",
          justifyContent: "right",
        }}
      />
    </TableContainer>
  );
};
