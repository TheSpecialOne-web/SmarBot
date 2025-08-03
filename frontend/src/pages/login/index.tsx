import { useAuth0 } from "@auth0/auth0-react";
import { Box, Button, Typography } from "@mui/material";
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import logo from "@/assets/logo.png";
import { Spacer } from "@/components/spacers/Spacer";
import { ERROR } from "@/const";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { theme } from "@/theme";

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { loginWithRedirect, isAuthenticated } = useAuth0();
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/main/chat");
    }

    const params = new URLSearchParams(location.search);
    const logoutReason = params.get("logout_reason");

    switch (logoutReason) {
      case ERROR.UNAUTHORIZED:
        enqueueErrorSnackbar({
          message: "セッションがタイムアウトしました。もう一度ログインしてください。",
        });
        break;
      case ERROR.FORBIDDEN:
        enqueueErrorSnackbar({
          message: "アクセスが禁止されています。組織管理者に連絡してください。",
        });
        break;
      default:
        break;
    }
  }, [isAuthenticated, navigate, enqueueErrorSnackbar]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 5,
        width: 400,
        backgroundColor: "white",
        boxShadow: `0 0 10px ${theme.palette.boxShadow.main}`,
        borderRadius: 1,
        boxSizing: "border-box",
      }}
    >
      <img src={logo} alt="Logo" style={{ width: "200px", height: "auto", margin: "40px 0" }} />
      <Spacer px={16} />
      <Typography textAlign="center">
        登録されたドキュメントを参考に、生成AIがあなたの質問にチャット形式でお答えします。回答に使われた文書も併せて確認することができます。
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={() => loginWithRedirect()}
        sx={{
          alignSelf: "center",
          width: 300,
          height: 50,
          fontSize: 20,
          padding: 3,
          mt: 2,
        }}
      >
        ログイン
      </Button>
    </Box>
  );
};

export default Login;
