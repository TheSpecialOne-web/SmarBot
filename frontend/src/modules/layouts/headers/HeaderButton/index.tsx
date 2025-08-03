import { Button, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";

type Props = {
  icon: React.ReactNode;
  text: string;
  href?: string;
  onClick?: () => void;
  isActive: boolean;
};

export const HeaderButton = ({ icon, text, href, onClick, isActive }: Props) => {
  return (
    <Button
      color="inherit"
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        color: isActive ? "primary.main" : grey[900],
        py: 0.5,
      }}
      href={href}
      onClick={onClick}
    >
      {icon}
      <Typography fontSize={10}>{text}</Typography>
    </Button>
  );
};
