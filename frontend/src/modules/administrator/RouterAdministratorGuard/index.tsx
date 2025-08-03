import { ReactNode, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useUserInfo } from "@/hooks/useUserInfo";

type Props = {
  component: ReactNode;
};

export const RouterAdministratorGuard = ({ component }: Props) => {
  const { userInfo } = useUserInfo();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!userInfo.is_administrator) {
      navigate("/main/chat");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userInfo, location]);

  return <>{component}</>;
};
