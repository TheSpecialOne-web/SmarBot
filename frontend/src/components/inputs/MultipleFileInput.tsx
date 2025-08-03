import React, { useRef } from "react";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";

type Props = {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  allowed_extension: string;
};

export const MultipleFileInput = ({ onChange, allowed_extension }: Props) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleOpenFileSelect = () => {
    inputRef.current?.click();
  };

  return (
    <>
      <PrimaryButton variant="outlined" text="ファイルを追加" onClick={handleOpenFileSelect} />
      <input
        type="file"
        hidden
        accept={allowed_extension}
        multiple
        ref={inputRef}
        onChange={onChange}
      />
    </>
  );
};
