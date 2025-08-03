import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import { Box, IconButton, Menu, MenuItem, PopoverOrigin, SxProps, Tooltip } from "@mui/material";
import { forwardRef, MouseEvent, ReactNode, useImperativeHandle, useState } from "react";

export type OptionsMenuItemTooltip = {
  title: string;
  placement?:
    | "bottom-end"
    | "bottom-start"
    | "bottom"
    | "left-end"
    | "left-start"
    | "left"
    | "right-end"
    | "right-start"
    | "right"
    | "top-end"
    | "top-start"
    | "top";
};

export type OptionsMenuItem = {
  onClick: () => void;
  disabled?: boolean;
  tooltip?: OptionsMenuItemTooltip;
  children: ReactNode;
  sx?: SxProps;
};

type Props = {
  items: OptionsMenuItem[];
  disabled?: boolean;
  icon?: ReactNode;
  anchorOrigin?: PopoverOrigin;
  buttonSx?: SxProps;
};

export const OptionsMenu = forwardRef<
  {
    handleClose: () => void;
  },
  Props
>(
  (
    {
      items,
      disabled,
      icon = <MoreHorizIcon />,
      anchorOrigin = {
        vertical: "bottom",
        horizontal: "left",
      },
      buttonSx,
    },
    ref,
  ) => {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: MouseEvent<HTMLElement>) => {
      event.stopPropagation();
      setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
      setAnchorEl(null);
    };

    useImperativeHandle(ref, () => ({
      handleClose,
    }));

    return (
      <Box onClick={e => e.stopPropagation()}>
        <IconButton onClick={handleClick} disabled={disabled} sx={buttonSx}>
          {icon}
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          anchorOrigin={anchorOrigin}
          open={open}
          onClose={handleClose}
          MenuListProps={{
            sx: {
              p: 0.5,
            },
          }}
        >
          {items.map((item, index) => (
            <Tooltip key={index} title={item.tooltip?.title} placement={item.tooltip?.placement}>
              <span>
                <MenuItem
                  onClick={e => {
                    e.stopPropagation();
                    item.onClick();
                  }}
                  disabled={item.disabled}
                  sx={item.sx}
                >
                  {item.children}
                </MenuItem>
              </span>
            </Tooltip>
          ))}
        </Menu>
      </Box>
    );
  },
);

// displayNameを設定
OptionsMenu.displayName = "OptionsMenu";
