import { DialogContent } from "@mui/material";
import dayjs from "dayjs";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { getComparator } from "@/libs/sort";
import { DocumentFolder } from "@/orval/models/backend-api";

const sortDocumentFolders = (
  documentFolders: DocumentFolder[],
  order: Order,
  orderBy: keyof DocumentFolder,
) => {
  const comparator = getComparator<DocumentFolder>(order, orderBy);
  return [...documentFolders].sort(comparator);
};

type Props = {
  open: boolean;
  onClose: () => void;
  documentFolders: DocumentFolder[];
  onSelect: (documentFolder: DocumentFolder) => void;
};

export const SelectDocumentFolderDialog = ({ open, onClose, documentFolders, onSelect }: Props) => {
  const tableColumns: CustomTableColumn<DocumentFolder>[] = [
    {
      key: "name",
      label: "フォルダ名",
      align: "left",
      sortFunction: sortDocumentFolders,
    },
    {
      key: "created_at",
      label: "作成日",
      align: "left",
      sortFunction: sortDocumentFolders,
      render: documentFolder => dayjs(documentFolder.created_at).format("YYYY年M月D日"),
    },
    {
      key: "id",
      label: "",
      align: "center",
      minWidth: 1,
      cellSx: { padding: 0 },
      render: documentFolder => (
        <PrimaryButton
          variant="outlined"
          text="選択"
          onClick={() => {
            onSelect(documentFolder);
          }}
        />
      ),
    },
  ];

  return (
    <CustomDialog title="フォルダを指定" open={open} onClose={onClose} maxWidth="md">
      <DialogContent>
        <CustomTable<DocumentFolder>
          tableColumns={tableColumns}
          tableData={documentFolders}
          maxTableHeight={600}
          hideControlHeader
          hideTablePagination
        />
      </DialogContent>
    </CustomDialog>
  );
};
