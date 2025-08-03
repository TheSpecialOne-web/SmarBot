import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import DriveFileMoveOutlinedIcon from "@mui/icons-material/DriveFileMoveOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import SyncIcon from "@mui/icons-material/Sync";
import { IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import { Document, DocumentFolder, DocumentStatus } from "@/orval/models/backend-api";

import { isDocumentFolder, isExternalDocumentFolder, TableRow } from "../types";

type Props = {
  row: TableRow;
  onClickUpdateDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickDeleteDocumentFolderIcon: (documenrFolder: DocumentFolder) => void;
  onClickMoveDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickResyncExternalDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickDeleteExternalDocumentFolderIcon: (documentFolder: DocumentFolder) => void;
  onClickUpdateDocumentIcon: (document: Document) => void;
  onClickDeleteDocumentIcon: (document: Document) => void;
  onClickMoveDocumentIcon: (document: Document) => void;
};

export const DocumentsTableAction = ({
  row,
  onClickUpdateDocumentFolderIcon,
  onClickDeleteDocumentFolderIcon,
  onClickMoveDocumentFolderIcon,
  onClickResyncExternalDocumentFolderIcon,
  onClickDeleteExternalDocumentFolderIcon,
  onClickUpdateDocumentIcon,
  onClickDeleteDocumentIcon,
  onClickMoveDocumentIcon,
}: Props) => {
  const { tmpUrsaPhase2 } = useFlags();
  const actionButtonDisabled =
    row.status === DocumentStatus.pending || row.status === DocumentStatus.deleting;
  const menuItems: OptionsMenuItem[] = isExternalDocumentFolder(row)
    ? [
        {
          onClick: () => onClickResyncExternalDocumentFolderIcon(row),
          children: (
            <Stack direction="row" gap={1}>
              <SyncIcon color="primary" />
              <Typography fontSize={14}>フォルダを再同期</Typography>
            </Stack>
          ),
        },
        {
          onClick: () => onClickDeleteExternalDocumentFolderIcon(row),
          children: (
            <Stack direction="row" gap={1}>
              <DeleteOutlineOutlinedIcon color="error" />
              <Typography fontSize={14}>連携解除</Typography>
            </Stack>
          ),
        },
      ]
    : isDocumentFolder(row)
    ? [
        {
          onClick: () => onClickUpdateDocumentFolderIcon(row),
          children: (
            <Stack direction="row" gap={1}>
              <EditOutlinedIcon color="primary" />
              <Typography fontSize={14}>フォルダ編集</Typography>
            </Stack>
          ),
        },
        {
          onClick: () => onClickMoveDocumentFolderIcon(row),
          children: (
            <Stack direction="row" gap={1}>
              <DriveFileMoveOutlinedIcon color="primary" />
              <Typography fontSize={14}>フォルダ移動</Typography>
            </Stack>
          ),
        },
        {
          onClick: () => onClickDeleteDocumentFolderIcon(row),
          children: (
            <Stack direction="row" gap={1}>
              <DeleteOutlineOutlinedIcon color="error" />
              <Typography fontSize={14}>フォルダ削除</Typography>
            </Stack>
          ),
        },
      ]
    : [
        {
          onClick: () => onClickUpdateDocumentIcon(row),
          disabled: actionButtonDisabled,
          children: (
            <Stack direction="row" gap={1}>
              <EditOutlinedIcon color="primary" />
              <Typography fontSize={14}>ドキュメント編集</Typography>
            </Stack>
          ),
        },
        {
          onClick: () => onClickMoveDocumentIcon(row),
          disabled: actionButtonDisabled,
          children: (
            <Stack direction="row" gap={1}>
              <DriveFileMoveOutlinedIcon color="primary" />
              <Typography fontSize={14}>ドキュメント移動</Typography>
            </Stack>
          ),
        },
        {
          onClick: () => onClickDeleteDocumentIcon(row),
          disabled: actionButtonDisabled,
          children: (
            <Stack direction="row" gap={1}>
              <DeleteOutlineOutlinedIcon color="error" />
              <Typography fontSize={14}>ドキュメント削除</Typography>
            </Stack>
          ),
        },
      ];

  return !tmpUrsaPhase2 ? (
    isDocumentFolder(row) || isExternalDocumentFolder(row) ? (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton
          onClick={() => onClickUpdateDocumentFolderIcon(row)}
          color="primary"
          sx={{ p: 0.5 }}
        >
          <EditOutlinedIcon />
        </IconButton>
        <IconButton
          onClick={() => onClickDeleteDocumentFolderIcon(row)}
          color="error"
          sx={{ p: 0.5 }}
        >
          <DeleteOutlineOutlinedIcon />
        </IconButton>
      </Stack>
    ) : (
      <Stack direction="row" gap={1} justifyContent="right">
        <Tooltip title={actionButtonDisabled && "処理中のドキュメントは編集できません"}>
          <span>
            <IconButton
              onClick={() => onClickUpdateDocumentIcon(row)}
              disabled={actionButtonDisabled}
              color="primary"
              sx={{ p: 0.5 }}
            >
              <EditOutlinedIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Tooltip title={actionButtonDisabled && "処理中のドキュメントは削除できません"}>
          <span>
            <IconButton
              onClick={() => onClickDeleteDocumentIcon(row)}
              disabled={actionButtonDisabled}
              color="error"
              sx={{ p: 0.5 }}
            >
              <DeleteOutlineOutlinedIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Stack>
    )
  ) : (
    <OptionsMenu items={menuItems} />
  );
};
