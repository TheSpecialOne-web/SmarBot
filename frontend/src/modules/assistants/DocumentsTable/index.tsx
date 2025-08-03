import FolderIcon from "@mui/icons-material/Folder";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { Link, Stack, Tooltip, Typography } from "@mui/material";
import dayjs from "dayjs";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import {
  Document,
  DocumentFolder,
  DocumentProcessingStats,
  DocumentStatus,
  ExternalDataConnectionType,
} from "@/orval/models/backend-api";
import { formatStorageUsage } from "@/utils/formatBytes";

import { DocumentsTableAction } from "./DocumentsTableAction";
import { ExternalDocumentFolderIcon } from "./ExternalDocumentFolderIcon";
import {
  createNullifiedDocument,
  createNullifiedDocumentFolder,
  isDocument,
  isDocumentFolder,
  TableRow,
} from "./types";

const sortFoldersAndDocuments = (tableRows: TableRow[], order: Order, orderBy: keyof TableRow) => {
  // フォルダが上に来るようにソート
  const comparator = getComparator<TableRow>(order, orderBy);
  return [...tableRows].sort((a, b) => {
    if (a.type === b.type) return comparator(a, b);
    return isDocumentFolder(a) ? -1 : 1;
  });
};

const filterDocumentsByQuery = (tableRows: TableRow[], query: string) => {
  return tableRows.filter(row => filterTest(query, [row.name ?? ""]));
};

const filterDocumentsByStatus = (tableRows: TableRow[], queries: string[]) => {
  if (queries.length === 0) {
    return tableRows.filter(row => isDocumentFolder(row));
  }
  return tableRows.filter(
    row => isDocumentFolder(row) || (isDocument(row) && queries.includes(row.status)),
  );
};

const displayDocumentStatus = (status: DocumentStatus) => {
  switch (status) {
    case DocumentStatus.pending:
      return "処理中";
    case DocumentStatus.completed:
      return "反映済み";
    case DocumentStatus.failed:
      return "エラー";
    case DocumentStatus.deleting:
      return "削除中";
  }
};

const displayExternalDocumentFolderStatus = ({
  num_completed_documents: numCompletedDocuments,
  num_deleting_documents: numDeletingDocuments,
  num_failed_documents: numFailedDocuments,
  num_total_documents: numTotalDocuments,
}: DocumentProcessingStats) => {
  const numProcessableDocuments = numTotalDocuments - numFailedDocuments - numDeletingDocuments;
  if (numProcessableDocuments === 0) {
    return `処理対象なし ${numFailedDocuments > 0 ? ` (${numFailedDocuments}件エラー)` : ""}`;
  }

  // e.g. "50% 処理済み (10件エラー)"
  const processedPercentage = (numCompletedDocuments / numProcessableDocuments) * 100;
  const formattedPercentage =
    processedPercentage % 1 === 0 ? processedPercentage.toFixed(0) : processedPercentage.toFixed(1);
  return `${formattedPercentage}% 処理済み${
    numFailedDocuments > 0 ? ` (${numFailedDocuments}件エラー)` : ""
  }`;
};

type Props = {
  documents: Document[];
  documentFolders: DocumentFolder[];
  onMoveToFolder: (folderId: string | null) => void;
  handleOpenPdf: (document: Document) => void;
  onClickUpdateDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickDeleteDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickMoveDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickResyncExternalDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickDeleteExternalDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickUpdateDocumentIcon: (document: Document) => void;
  onClickDeleteDocumentIcon: (document: Document) => void;
  onClickMoveDocumentIcon: (document: Document) => void;
  onClickExternalDocumentFolder: (
    folderId: string,
    externalType: ExternalDataConnectionType,
  ) => void;
  hasWritePolicy: boolean;
  selectedRowIds: TableRow["id"][];
  handleSelectRow: (selectedRowIds: number[]) => void;
  isLoading: boolean;
};

export const DocumentsTable = ({
  documents,
  documentFolders,
  onMoveToFolder,
  handleOpenPdf,
  onClickUpdateDocumentFolderIcon,
  onClickDeleteDocumentFolderIcon,
  onClickMoveDocumentFolderIcon,
  onClickResyncExternalDocumentFolderIcon,
  onClickDeleteExternalDocumentFolderIcon,
  onClickUpdateDocumentIcon,
  onClickDeleteDocumentIcon,
  onClickMoveDocumentIcon,
  onClickExternalDocumentFolder,
  hasWritePolicy,
  selectedRowIds,
  handleSelectRow,
  isLoading,
}: Props) => {
  const tableColumns: CustomTableColumn<TableRow>[] = [
    {
      key: "name",
      label: "名前",
      align: "left",
      render: row => {
        if (isDocument(row)) {
          return (
            <Stack direction="row" gap={1} alignItems="center">
              <InsertDriveFileIcon sx={{ fontSize: 24 }} color="secondary" />
              <Link onClick={() => handleOpenPdf(row)} sx={{ cursor: "pointer" }}>
                {row.name}.{row.file_extension}
              </Link>
            </Stack>
          );
        }
        if (row.external_id) {
          return (
            <Stack direction="row" gap={1} alignItems="center">
              <ExternalDocumentFolderIcon
                externalDataConnectionType={row.external_data_connection_type}
              />
              <Tooltip
                title={<Typography variant="body2">外部データソースのページを開く</Typography>}
                placement="top"
                arrow
              >
                <Link
                  onClick={() =>
                    row.external_data_connection_type &&
                    onClickExternalDocumentFolder(row.id, row.external_data_connection_type)
                  }
                  sx={{ cursor: "pointer" }}
                >
                  {row.name}
                </Link>
              </Tooltip>
            </Stack>
          );
        }
        return (
          <Stack direction="row" gap={1} alignItems="center">
            <FolderIcon sx={{ fontSize: 24 }} color="secondary" />
            <Link onClick={() => onMoveToFolder(row.id)} sx={{ cursor: "pointer" }}>
              {row.name}
            </Link>
          </Stack>
        );
      },
      sortFunction: sortFoldersAndDocuments,
    },
    {
      key: "creator",
      label: "作成者",
      align: "left",
      render: row => {
        if (isDocument(row)) return row.creator?.name ?? "-";
        return "-";
      },
    },
    {
      key: "created_at",
      label: "追加日",
      align: "left",
      render: row => {
        return <Typography>{dayjs(row.created_at).format("YYYY年M月D日")}</Typography>;
      },
      sortFunction: sortFoldersAndDocuments,
      minWidth: 220,
    },
    {
      key: "memo",
      label: "メモ",
      align: "left",
      render: row => {
        if (isDocument(row)) return row.memo ?? "";
        return "";
      },
    },
    {
      key: "storage_usage",
      label: (
        <>
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: "bold",
              width: "fit-content",
              textWrap: "nowrap",
            }}
          >
            ストレージ容量
          </Typography>
          <Spacer px={4} horizontal />
          <IconButtonWithTooltip
            tooltipTitle="ドキュメントが使用しているストレージ容量の概算を表します。正確な値は未知なため、おおよその目安としてご利用ください。"
            color="primary"
            icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
            iconButtonSx={{ p: 0.5 }}
          />
        </>
      ),
      align: "left",
      render: row => {
        if (isDocument(row)) return row.storage_usage ? formatStorageUsage(row.storage_usage) : "-";
        return "-";
      },
      sortFunction: sortFoldersAndDocuments,
    },
    {
      key: "status",
      label: "ステータス",
      align: "left",
      render: row => {
        if (isDocument(row)) {
          return displayDocumentStatus(row.status);
        }
        if (isDocumentFolder(row) && row.document_processing_stats) {
          return displayExternalDocumentFolderStatus(row.document_processing_stats);
        }
        return "-";
      },
      columnFilterProps: {
        filterItems: Object.values(DocumentStatus).map(status => ({
          key: status,
          label: displayDocumentStatus(status),
        })),
        filterFunction: filterDocumentsByStatus,
      },
    },
  ];

  const renderActionColumn = (row: TableRow) => {
    return (
      <DocumentsTableAction
        row={row}
        onClickUpdateDocumentFolderIcon={onClickUpdateDocumentFolderIcon}
        onClickDeleteDocumentFolderIcon={onClickDeleteDocumentFolderIcon}
        onClickMoveDocumentFolderIcon={onClickMoveDocumentFolderIcon}
        onClickResyncExternalDocumentFolderIcon={onClickResyncExternalDocumentFolderIcon}
        onClickDeleteExternalDocumentFolderIcon={onClickDeleteExternalDocumentFolderIcon}
        onClickUpdateDocumentIcon={onClickUpdateDocumentIcon}
        onClickDeleteDocumentIcon={onClickDeleteDocumentIcon}
        onClickMoveDocumentIcon={onClickMoveDocumentIcon}
      />
    );
  };

  const tableData: TableRow[] = [
    ...documentFolders.map(documentFolder => ({
      ...createNullifiedDocument(),
      type: "documentFolder" as const,
      ...documentFolder,
    })),
    ...documents.map(document => ({
      ...createNullifiedDocumentFolder(),
      type: "document" as const,
      ...document,
    })),
  ];

  const setSelectedRowIds = (rowIds: TableRow["id"][]) => {
    const rowIdsNumber = rowIds.filter((id): id is number => typeof id === "number");
    handleSelectRow(rowIdsNumber);
  };

  if (isLoading) {
    return <CustomTableSkeleton />;
  }

  return (
    <CustomTable<TableRow>
      tableColumns={tableColumns}
      tableData={tableData}
      searchFilter={filterDocumentsByQuery}
      defaultSortProps={{ key: "created_at", order: "desc" }}
      renderActionColumn={hasWritePolicy ? renderActionColumn : undefined}
      checkboxProps={
        hasWritePolicy && documents.length > 0
          ? {
              selectedRowIds: selectedRowIds,
              setSelectedRowIds: setSelectedRowIds,
              isCheckable: (row: TableRow) => isDocument(row),
            }
          : undefined
      }
    />
  );
};
