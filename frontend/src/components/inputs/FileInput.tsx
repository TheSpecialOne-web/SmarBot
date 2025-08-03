import { Box, Button, Typography } from "@mui/material";

type Props = {
  file: File | null;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  allowedExtension?: "pdf" | "csv";
};

export const FileInput = ({ file, onChange, allowedExtension = "csv" }: Props) => {
  return (
    <Box
      sx={{
        border: "1px dashed",
        borderColor: "divider",
        borderRadius: 2,
        px: 2,
        py: 4,
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
      component="label"
    >
      {file && <Typography variant="subtitle1">・{file.name}</Typography>}
      <label>
        <Button variant="outlined" component="span" sx={{ mt: file ? 2 : 0 }}>
          {file ? "ファイルを変更" : "ファイルを選択"}
        </Button>
        <input type="file" hidden accept={`.${allowedExtension}`} onChange={onChange} />
      </label>
    </Box>
  );
};
