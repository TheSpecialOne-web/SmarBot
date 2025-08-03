import { useState } from "react";

import { createAttachments } from "@/orval/backend-api";
import { Attachment } from "@/orval/models/backend-api";

export type ImageFile = {
  name: string;
  base64Url: string;
};

export const useAttachment = (botId: number) => {
  const [uploadedAttachments, setUploadedAttachments] = useState<Attachment[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[] | null>(null);
  const [imageFiles, setImageFiles] = useState<ImageFile[]>([]);
  const [isUploadingAttachments, setIsUploadingAttachments] = useState(false);

  const resetAttachments = () => {
    setUploadedAttachments([]);
  };

  const removeAttachment = (attachmentId: Attachment["id"]): Attachment[] => {
    const currentAttachments = uploadedAttachments.filter(
      attachment => attachment.id !== attachmentId,
    );
    setUploadedAttachments(currentAttachments);
    return currentAttachments;
  };

  const uploadAttachments = async (files: File[]): Promise<Attachment[]> => {
    if (!files || files.length === 0) return [];

    const fileArray = Array.from(files);
    const filteredFiles = fileArray.filter(
      file => !uploadedAttachments?.some(attachment => attachment.name === file.name),
    );
    if (filteredFiles.length === 0) {
      return [];
    }
    setSelectedFiles(filteredFiles);
    filteredFiles.forEach(file => {
      // 画像ファイルの場合、base64Urlを取得
      if (!file.type.startsWith("image")) return [];
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64Url = reader.result as string;
        setImageFiles(prev => [...prev, { name: file.name, base64Url }]);
      };
    });

    setIsUploadingAttachments(true);
    try {
      const { attachments } = await createAttachments(botId, { files: filteredFiles });
      if (!attachments) return [];
      const currentAttachments = [...(uploadedAttachments || []), ...attachments].filter(
        (attachment, index, self) => index === self.findIndex(a => a.id === attachment.id),
      );
      setUploadedAttachments(currentAttachments);
      return currentAttachments;
    } finally {
      setIsUploadingAttachments(false);
      setSelectedFiles(null);
    }
  };

  return {
    uploadedAttachments,
    selectedFiles,
    imageFiles,
    isUploadingAttachments,
    uploadAttachments,
    resetAttachments,
    removeAttachment,
  };
};
