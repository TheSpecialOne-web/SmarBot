import BuildIcon from "@mui/icons-material/Build";
import { Box, Modal, Typography } from "@mui/material";

export const MaintenanceModal = () => {
  return (
    <Modal
      open={true}
      aria-labelledby="maintenance-modal-title"
      aria-describedby="maintenance-modal-description"
    >
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: 400,
          bgcolor: "background.paper",
          boxShadow: 24,
          p: 4,
          outline: "none",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <BuildIcon sx={{ fontSize: 60, color: "action.active" }} />
        <Typography id="maintenance-modal-title" variant="h2" sx={{ mt: 2 }}>
          メンテナンス中
        </Typography>
        <Typography id="maintenance-modal-description" sx={{ mt: 2 }}>
          ただいまメンテナンス中です。ご不便をおかけして申し訳ございません。作業完了までしばらくお待ちください。
        </Typography>
      </Box>
    </Modal>
  );
};
