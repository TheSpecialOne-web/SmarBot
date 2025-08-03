import { LoadingButton, LoadingButtonProps } from "@mui/lab";
import { FC, ReactNode } from "react";

export type BaseButtonProps = Pick<
  LoadingButtonProps,
  | "color"
  | "size"
  | "variant"
  | "type"
  | "loading"
  | "fullWidth"
  | "disabled"
  | "startIcon"
  | "endIcon"
  | "onClick"
  | "href"
> & { text: ReactNode };

export const BaseButton: FC<BaseButtonProps> = ({
  text,
  color,
  size = "medium",
  variant = "contained",
  type = "button",
  loading,
  fullWidth,
  disabled,
  startIcon,
  endIcon,
  onClick,
  href,
}) => (
  <LoadingButton
    color={color}
    size={size}
    variant={variant}
    type={type}
    loading={loading}
    fullWidth={fullWidth}
    disabled={disabled}
    startIcon={startIcon}
    endIcon={endIcon}
    onClick={onClick}
    href={href}
  >
    {text}
  </LoadingButton>
);
