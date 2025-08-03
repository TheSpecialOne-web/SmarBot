import SearchIcon from "@mui/icons-material/Search";
import { InputAdornment, TextField } from "@mui/material";
import { ChangeEvent } from "react";

type Props = {
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  fullWidth?: boolean;
  size?: "small" | "medium";
  text?: string;
  borderRadius?: number;
};

export const SearchField = ({
  value,
  onChange,
  fullWidth = false,
  size = "small",
  text = "検索...",
  borderRadius = 1,
}: Props) => {
  return (
    <TextField
      fullWidth={fullWidth}
      size={size}
      variant="outlined"
      placeholder={text}
      sx={{
        bgcolor: "background.paper",
        borderRadius: borderRadius,
        "& .MuiOutlinedInput-root": {
          "& fieldset": {
            borderRadius: borderRadius,
          },
        },
      }}
      value={value}
      onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e)}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
        sx: {
          alignItems: "center",
          paddingRight: "8px",
        },
      }}
    />
  );
};
