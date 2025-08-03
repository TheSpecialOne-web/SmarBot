import { Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { Control } from "react-hook-form";

import { CustomTextField } from "@/components/inputs/CustomTextField";

type Props = {
  isEditing: boolean;
  title: string;
  control: Control<{ title: string }>;
  onSubmit: (data: { title: string }) => Promise<void>;
};

export const ConversationTitle = ({ isEditing, title, control, onSubmit: onSubmitProp }: Props) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isComposing, setIsComposing] = useState(false);

  const { handleSubmit } = control;
  const onSubmit = async (data: { title: string }) => {
    inputRef.current?.blur();
    onSubmitProp(data);
  };

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus();
    }
  }, [isEditing]);

  return isEditing ? (
    <CustomTextField
      name="title"
      control={control}
      variant="standard"
      color="secondary"
      fullWidth
      onBlur={e => {
        e.preventDefault();
        handleSubmit(onSubmit)();
      }}
      onCompositionStart={() => setIsComposing(true)}
      onCompositionEnd={() => setIsComposing(false)}
      onKeyDown={e => {
        if (e.key === "Enter" && !isComposing) {
          e.preventDefault();
          handleSubmit(onSubmit)();
        }
      }}
      inputRef={inputRef}
      inputProps={{
        sx: {
          p: 0,
          fontSize: "13px",
          fontWeight: 500,
        },
      }}
    />
  ) : (
    <Typography
      variant="subtitle2"
      width="100%"
      whiteSpace="nowrap"
      overflow="hidden"
      textOverflow="fade"
      sx={{
        maskImage: "linear-gradient(to right, black 80%, transparent 100%)",
      }}
    >
      {title}
    </Typography>
  );
};
