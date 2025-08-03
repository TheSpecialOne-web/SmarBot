import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import { Link, MenuListProps, Typography } from "@mui/material";
import Menu from "@mui/material/Menu";
import React, { ReactNode, useState } from "react";

import { PrimaryButton } from "../buttons/PrimaryButton";

type Props = {
  component?: "button" | "link";
  title: string | ReactNode;
  startIcon?: ReactNode;
  children: ReactNode;
  MenuListProps?: Partial<MenuListProps>;
};

export const ExpandableMenu = ({
  component = "button",
  title,
  startIcon,
  children,
  MenuListProps,
}: Props) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const open = Boolean(anchorEl);

  return (
    <>
      {component === "button" ? (
        <PrimaryButton
          variant="outlined"
          onClick={(event: React.MouseEvent<HTMLElement>) => {
            setAnchorEl(event.currentTarget);
          }}
          text={
            typeof title === "string" ? <Typography variant="button">{title}</Typography> : title
          }
          startIcon={startIcon}
          endIcon={open ? <ArrowDropUpIcon /> : <ArrowDropDownIcon />}
        />
      ) : component === "link" ? (
        <Link
          component="button"
          onClick={(event: React.MouseEvent<HTMLElement>) => {
            setAnchorEl(event.currentTarget);
          }}
        >
          {title}
        </Link>
      ) : null}
      <Menu
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "left",
        }}
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        onClick={() => setAnchorEl(null)}
        MenuListProps={MenuListProps}
      >
        {children}
      </Menu>
    </>
  );
};
