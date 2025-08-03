import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";
import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { Link, Menu, Stack } from "@mui/material";
import { useState } from "react";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { DocumentToDisplay } from "@/types/document";

type Props = {
  documentToDisplay: Required<Pick<DocumentToDisplay, "documentFolderDetail">>;
  onMoveToFolder: (folderId: string | null) => void;
};

export const FolderMenu = ({ documentToDisplay, onMoveToFolder }: Props) => {
  const [openMenu, setOpenMenu] = useState<boolean>(false);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(true);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu(false);
  };

  return (
    <>
      <IconButtonWithTooltip
        tooltipTitle="ドキュメントの場所"
        icon={<FolderOutlinedIcon fontSize="small" />}
        iconButtonSx={{ fontsize: "small" }}
        onClick={openMenu ? handleClose : handleOpen}
      />
      <Menu
        id="folder-menu"
        anchorEl={anchorEl}
        open={openMenu}
        onClose={handleClose}
        onClick={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        sx={{
          "& .MuiPaper-root": {
            width: "fit-content",
          },
        }}
      >
        <Stack direction="row" alignItems="center" gap={0.5} px={2}>
          <Link
            onClick={() => onMoveToFolder(null)}
            sx={{ cursor: "pointer", textDecoration: "none" }}
          >
            <Stack justifyContent="center">
              <HomeOutlinedIcon fontSize="small" />
            </Stack>
          </Link>
          {documentToDisplay.documentFolderDetail.ancestor_document_folders.map(({ id, name }) => (
            <Stack key={id} direction="row" alignItems="center" gap={0.5}>
              <KeyboardArrowRightIcon fontSize="small" color="secondary" />
              <Link
                onClick={() => onMoveToFolder(id)}
                sx={{ cursor: "pointer", textDecoration: "none" }}
              >
                {name}
              </Link>
            </Stack>
          ))}
          {documentToDisplay.documentFolderDetail.name && (
            <Stack direction="row" alignItems="center" gap={0.5}>
              <KeyboardArrowRightIcon fontSize="small" color="secondary" />
              <Link
                onClick={() => onMoveToFolder(documentToDisplay.documentFolderDetail?.id ?? null)}
                sx={{ cursor: "pointer", textDecoration: "none" }}
              >
                {documentToDisplay.documentFolderDetail.name}
              </Link>
            </Stack>
          )}
        </Stack>
      </Menu>
    </>
  );
};
