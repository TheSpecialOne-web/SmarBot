import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { IconButton, Link, Stack } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { CommonDocumentTemplate } from "@/orval/models/administrator-api";
import { formatDate } from "@/utils/formatDate";

type Props = {
  documentTemplates: CommonDocumentTemplate[];
  getDocuments: () => void;
  onClickDeleteIcon: (document: CommonDocumentTemplate) => void;
  onClickUpdateIcon: (document: CommonDocumentTemplate) => void;
  onClickDocument: (document: CommonDocumentTemplate) => void;
};

export const CommonDocumentTemplatesTable = ({
  documentTemplates,
  onClickDeleteIcon,
  onClickUpdateIcon,
  onClickDocument,
}: Props) => {
  const sortCommonDocumentTemplates = (
    documents: CommonDocumentTemplate[],
    order: Order,
    orderBy: keyof CommonDocumentTemplate,
  ) => {
    const comparator = getComparator<CommonDocumentTemplate>(order, orderBy);
    return [...documents].sort(comparator);
  };

  const filterCommonDocumentTemplate = (documents: CommonDocumentTemplate[], query: string) => {
    return documents.filter(document => {
      return filterTest(query, [document.blob_name]);
    });
  };

  const tableColumns: CustomTableColumn<CommonDocumentTemplate>[] = [
    {
      key: "blob_name",
      label: "ドキュメント名",
      align: "left",
      render: document => {
        return (
          <Link sx={{ cursor: "pointer" }} onClick={() => onClickDocument(document)}>
            {document.blob_name}
          </Link>
        );
      },
      sortFunction: sortCommonDocumentTemplates,
    },
    {
      key: "created_at",
      label: "追加日",
      align: "left",
      render: document => {
        return formatDate(document.created_at);
      },
      sortFunction: sortCommonDocumentTemplates,
    },
    {
      key: "memo",
      label: "メモ",
      align: "left",
      sortFunction: sortCommonDocumentTemplates,
    },
  ];

  const renderActionColumn = (document: CommonDocumentTemplate) => {
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton onClick={() => onClickUpdateIcon(document)} color="primary">
          <EditOutlinedIcon />
        </IconButton>
        <span>
          <IconButton onClick={() => onClickDeleteIcon(document)} color="error">
            <DeleteOutlineOutlinedIcon />
          </IconButton>
        </span>
      </Stack>
    );
  };

  return (
    <CustomTable<CommonDocumentTemplate>
      tableColumns={tableColumns}
      tableData={documentTemplates}
      searchFilter={filterCommonDocumentTemplate}
      defaultSortProps={{ key: "created_at", order: "desc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
