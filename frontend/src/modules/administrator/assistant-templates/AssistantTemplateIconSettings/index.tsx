import { CachedRounded, Clear } from "@mui/icons-material";
import UploadFileRoundedIcon from "@mui/icons-material/UploadFileRounded";
import { IconButton, Stack, Tooltip } from "@mui/material";
import { ChangeEvent, useRef } from "react";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";

type Props = {
  setFormIcon: (icon: File) => void;
  iconColor: string;
  setFormIconColor: (iconColor: string) => void;
  iconUrl: string | null;
  deleteIcon: () => void;
};

export const AssistantTemplateIconSettings = ({
  setFormIcon,
  iconColor,
  setFormIconColor,
  iconUrl,
  deleteIcon,
}: Props) => {
  const iconInputRef = useRef<HTMLInputElement>(null);

  const onIconChange = (e: ChangeEvent<HTMLInputElement>) => {
    const image = e.target.files?.[0];
    if (image) {
      setFormIcon(image);
    }
  };

  const onIconColorChange = () => {
    const randomColor = Math.floor(Math.random() * 0xffffff).toString(16);
    setFormIconColor(`#${randomColor}`);
  };

  return (
    <Stack direction="row" sx={{ position: "relative", width: "fit-content" }}>
      <Tooltip title={iconUrl ? "アイコンを変更する" : "アイコンをアップロードする"} arrow>
        <IconButton
          onClick={() => iconInputRef.current?.click()}
          sx={{ p: 0, width: "fit-content" }}
        >
          <AssistantAvatar size={60} iconUrl={iconUrl || undefined} iconColor={iconColor} />
          <input
            type="file"
            hidden
            accept=".jpg, .jpeg, .png"
            ref={iconInputRef}
            onChange={onIconChange}
          />
          <UploadFileRoundedIcon
            color="primary"
            sx={{ position: "absolute", bottom: -8, right: -8 }}
          />
        </IconButton>
      </Tooltip>
      {iconUrl ? (
        <IconButton onClick={deleteIcon} sx={{ position: "absolute", p: 0.5, top: -8, right: -8 }}>
          <Clear fontSize="small" />
        </IconButton>
      ) : (
        <IconButton
          onClick={onIconColorChange}
          sx={{ position: "absolute", p: 0, top: -8, left: -8 }}
        >
          <CachedRounded />
        </IconButton>
      )}
    </Stack>
  );
};
