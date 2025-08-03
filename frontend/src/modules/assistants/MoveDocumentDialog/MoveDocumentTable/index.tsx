import ArrowForwardIosOutlinedIcon from "@mui/icons-material/ArrowForwardIosOutlined";
import FolderIcon from "@mui/icons-material/Folder";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { Button, Container, IconButton, Link, Stack, Typography } from "@mui/material";
import { useCallback } from "react";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import {
  Document,
  DocumentFolder,
  DocumentFolderDetail,
  MoveDocumentParam,
} from "@/orval/models/backend-api";

import { DocumentFolderBreadcrumbs } from "../../DocumentManagement/DocumentFolderBreadcrumbs";
import {
  createNullifiedDocument,
  createNullifiedDocumentFolder,
  isDocument,
  isDocumentFolder,
  TableRow,
} from "../../DocumentsTable/types";

type Props = {
  rootDocumentFolder: DocumentFolder;
  documents: Document[];
  documentFolders: DocumentFolder[];
  displayedDocumentFolderDetail?: DocumentFolderDetail;
  currentParentDocumentFolderDetail: DocumentFolderDetail;
  onMoveToFolder: (folderId: string) => void;
  onSubmit: (param: MoveDocumentParam) => void;
  onClose: () => void;
  isLoading: boolean;
};

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

export const MoveDocumentTable = ({
  rootDocumentFolder,
  documents,
  documentFolders,
  displayedDocumentFolderDetail,
  currentParentDocumentFolderDetail,
  onMoveToFolder,
  onSubmit,
  onClose,
  isLoading,
}: Props) => {
  const tableColumns: CustomTableColumn<TableRow>[] = [
    {
      key: "name",
      label: "名前",
      align: "left",
      render: useCallback(
        (row: TableRow) => {
          if (isDocument(row)) {
            return (
              <Stack direction="row" gap={1} alignItems="center">
                <InsertDriveFileIcon sx={{ fontSize: 24 }} color="secondary" />
                <Typography>
                  {row.name}.{row.file_extension}
                </Typography>
              </Stack>
            );
          }
          return (
            <Stack direction="row" gap={1} alignItems="center">
              <FolderIcon sx={{ fontSize: 24 }} color="secondary" />
              {row.id === currentParentDocumentFolderDetail.id ? (
                <Typography>{row.name}</Typography>
              ) : (
                <Link onClick={() => onMoveToFolder(row.id)} sx={{ cursor: "pointer" }}>
                  {row.name}
                </Link>
              )}
            </Stack>
          );
        },
        [onMoveToFolder, currentParentDocumentFolderDetail.id],
      ),
      sortFunction: sortFoldersAndDocuments,
    },
  ];

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

  const renderActionColumn = (row: TableRow) => {
    if (!isDocumentFolder(row)) {
      return null;
    }
    return (
      <Stack direction="row" gap={1} alignContent="center">
        <Button
          variant="outlined"
          color="primary"
          onClick={() => onSubmit({ document_folder_id: row.id })}
          disabled={
            row.id === currentParentDocumentFolderDetail.id ||
            row.id === currentParentDocumentFolderDetail?.id
          }
        >
          移動
        </Button>
        <IconButton
          onClick={() => onMoveToFolder(row.id)}
          disabled={row.id === currentParentDocumentFolderDetail.id}
        >
          <ArrowForwardIosOutlinedIcon />
        </IconButton>
      </Stack>
    );
  };

  if (isLoading || !displayedDocumentFolderDetail) {
    return (
      <Container sx={{ py: 4 }}>
        <CustomTableSkeleton />
      </Container>
    );
  }

  return (
    <>
      <CustomDialogContent>
        <ContentHeader>
          <Stack direction="row">
            <Typography variant="h5">移動先：</Typography>
            {displayedDocumentFolderDetail && (
              <DocumentFolderBreadcrumbs
                documentFolderDetail={displayedDocumentFolderDetail}
                rootDocumentFolderId={rootDocumentFolder.id}
                onMoveToFolder={onMoveToFolder}
              />
            )}
          </Stack>
        </ContentHeader>
        <CustomTable<TableRow>
          hideTablePagination={true}
          tableColumns={tableColumns}
          tableData={tableData}
          searchFilter={filterDocumentsByQuery}
          defaultSortProps={{ key: "created_at", order: "desc" }}
          renderActionColumn={renderActionColumn}
          showRenderActionOnHover={true}
        />
      </CustomDialogContent>
      <CustomDialogAction
        onSubmit={() => onSubmit({ document_folder_id: displayedDocumentFolderDetail.id })}
        onClose={onClose}
        buttonText="移動"
        disabled={
          !displayedDocumentFolderDetail.id ||
          currentParentDocumentFolderDetail?.id === displayedDocumentFolderDetail.id
        }
      />
    </>
  );
};
