import { Send as SendIcon } from "@mui/icons-material";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import StopCircleOutlinedIcon from "@mui/icons-material/StopCircleOutlined";
import { IconButton, Stack, TextField } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import type { KeyboardEvent } from "react";
import { ChangeEvent, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { useFormContext } from "react-hook-form";
import { LuFolderSearch } from "react-icons/lu";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import {
  ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
  ALLOWED_ATTACHMENT_FILE_EXTENSIONS_FOR_PYPDF,
} from "@/const";
import { useAttachment } from "@/hooks/useAttachment";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useScreen } from "@/hooks/useScreen";
import { useUserInfo } from "@/hooks/useUserInfo";
import { isChatGptBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { useGetDocumentFolders } from "@/orval/backend-api";
import {
  Approach,
  Attachment,
  Bot,
  DocumentFolder,
  PdfParser,
  UserTenant,
} from "@/orval/models/backend-api";

import { ChatAttachments } from "./ChatAttachments";
import { ChatDocumentFolder } from "./ChatDocumentFolder";
import { SelectDocumentFolderDialog } from "./SelectDocumentFolderDialog";

const getAllowedExtensions = (tenant: UserTenant, bot: Bot): string[] => {
  if (
    isChatGptBot(bot) &&
    ([PdfParser.document_intelligence, PdfParser.llm_document_reader] as string[]).includes(
      tenant.basic_ai_pdf_parser,
    )
  ) {
    return Object.values(ALLOWED_ATTACHMENT_FILE_EXTENSIONS);
  }
  if (
    !isChatGptBot(bot) &&
    ([PdfParser.document_intelligence, PdfParser.llm_document_reader] as string[]).includes(
      bot.pdf_parser,
    )
  ) {
    return Object.values(ALLOWED_ATTACHMENT_FILE_EXTENSIONS);
  }
  return Object.values(ALLOWED_ATTACHMENT_FILE_EXTENSIONS_FOR_PYPDF);
};

type Props = {
  bot: Bot;
  onSend: (
    question: string,
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
  ) => Promise<void>;
  stoppable: boolean;
  onStopChat: () => void;
  enableAttachment?: boolean;
  enableDocumentFolder?: boolean;
};

export type ChatQuestionFormParams = {
  question: string;
  attachmentIds?: Attachment["id"][];
  documentFolder?: DocumentFolder;
};

const MENU_ITEM_HEIGHT = 36;
const MENU_PADDING = 8;

export const ChatQuestionForm = ({
  bot,
  onSend,
  stoppable,
  onStopChat,
  enableAttachment = false,
  enableDocumentFolder = true,
}: Props) => {
  const optionsMenuRef = useRef<{ handleClose: () => void }>(null);
  const { isTablet } = useScreen();
  const iconButtonSpacing = isTablet ? undefined : { mb: 1, mx: 1 };
  const { chatWithPdfFiles } = useFlags();
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const { userInfo } = useUserInfo();

  const {
    isUploadingAttachments,
    uploadedAttachments,
    selectedFiles,
    imageFiles,
    uploadAttachments,
    resetAttachments,
    removeAttachment,
  } = useAttachment(bot.id);

  const documentFolderOptionEnabled =
    enableDocumentFolder && ([Approach.neollm, Approach.ursa] as string[]).includes(bot.approach);

  const { data: documentFoldersData, error: getDocumentFoldersError } = useGetDocumentFolders(
    bot.id,
    { parent_document_folder_id: undefined },
    {
      swr: {
        enabled: !Number.isNaN(bot.id) && documentFolderOptionEnabled,
        onSuccess: () => {
          onRemoveDocumentFolder();
        },
      },
    },
  );
  if (getDocumentFoldersError) {
    const errMsg = getErrorMessage(getDocumentFoldersError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダの取得に失敗しました。" });
  }
  const documentFolders = documentFoldersData?.document_folders ?? [];

  const {
    register,
    handleSubmit,
    formState: { isValid },
    setValue,
    getValues,
    trigger,
    watch,
    setFocus,
  } = useFormContext<ChatQuestionFormParams>();

  const selectedDocumentFolder = watch("documentFolder");

  const {
    isOpen: isOpenSelectDocumentFolderDialog,
    open: openCreateUserDialog,
    close: closeSelectDocumentFolderDialog,
  } = useDisclosure({});

  useEffect(() => {
    if (setFocus) setFocus("question");
  }, [bot, setFocus]);

  const onSubmit = async ({ question, attachmentIds, documentFolder }: ChatQuestionFormParams) => {
    if (stoppable) return;
    // 添付ファイルまたは質問が必須
    if (attachmentIds?.length === 0 && !question?.trim()) return;
    const attachments = uploadedAttachments?.filter(attachment =>
      attachmentIds?.includes(attachment.id),
    );
    onSend(question, attachments, documentFolder);
    resetAttachments();
  };

  const onEnterPress = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(onSubmit)();
    }
  };

  const handleUploadAttachments = async (files: File[]) => {
    try {
      const attachments = await uploadAttachments(files);
      setValue(
        "attachmentIds",
        attachments.map(attachment => attachment.id),
      );
      trigger("question");
      setFocus("question");
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({
        message: errMsg || "ファイルのアップロードに失敗しました。",
      });
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current!.value = "";
      }
    }
  };

  const onFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (optionsMenuRef.current) {
      optionsMenuRef.current.handleClose();
    }
    if (!event.target.files) return;
    handleUploadAttachments(Array.from(event.target.files));
  };

  const onRemoveAttachment = (attachmentId: Attachment["id"]) => {
    const attachments = removeAttachment(attachmentId);
    setValue(
      "attachmentIds",
      attachments.map(attachment => attachment.id),
    );
    trigger("question");
  };

  const onRemoveDocumentFolder = () => {
    setValue("documentFolder", undefined);
  };

  const onDrop = (files: File[]) => {
    handleUploadAttachments(files);
  };

  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInputEnabled = chatWithPdfFiles && enableAttachment;

  const { getRootProps } = useDropzone({ onDrop, noClick: true, disabled: !fileInputEnabled });

  // userInfo is undefined if embedded in iframe
  const allowedExtensions = userInfo ? getAllowedExtensions(userInfo.tenant, bot) : [];

  const attachmentOptionItem: OptionsMenuItem = {
    children: (
      <Stack direction="row" gap={1}>
        <AttachFileIcon />
        ファイルを添付
        <input
          type="file"
          hidden
          accept={allowedExtensions.map(extension => `.${extension}`).join(", ")}
          multiple
          ref={fileInputRef}
          onChange={onFileChange}
        />
      </Stack>
    ),
    onClick: () => {
      fileInputRef.current?.click();
    },
    tooltip: {
      title: `ファイル形式は${allowedExtensions.join(", ")}のみ対応しています`,
      placement: "top",
    },
  };

  const documentFolderOptionItem: OptionsMenuItem = {
    children: (
      <Stack direction="row" gap={1}>
        <LuFolderSearch
          size={24}
          style={{
            paddingLeft: 2,
            paddingRight: 2,
          }}
        />
        フォルダを指定
      </Stack>
    ),
    onClick: () => {
      openCreateUserDialog();
      if (optionsMenuRef.current) {
        optionsMenuRef.current.handleClose();
      }
    },
  };

  const optionItems: OptionsMenuItem[] = [
    fileInputEnabled && attachmentOptionItem,
    documentFolderOptionItem,
  ].filter(Boolean);

  const showChatAttachments =
    uploadedAttachments.length > 0 || (isUploadingAttachments && selectedFiles);

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} {...(fileInputEnabled ? getRootProps() : {})}>
        <Stack
          sx={{
            borderWidth: "1px",
            borderStyle: "solid",
            borderColor: "rgba(0, 0, 0, 0.4)",
            borderRadius: 2,
            bgcolor: "background.paper",
          }}
        >
          {(selectedDocumentFolder || showChatAttachments) && (
            <Stack direction="row" gap={1} sx={{ pl: 1, pt: 1 }}>
              {selectedDocumentFolder && (
                <ChatDocumentFolder
                  selectedDocumentFolder={selectedDocumentFolder}
                  onRemove={onRemoveDocumentFolder}
                />
              )}
              {showChatAttachments && (
                <ChatAttachments
                  uploadedAttachments={uploadedAttachments}
                  selectedFiles={selectedFiles}
                  imageFiles={imageFiles}
                  isUploading={isUploadingAttachments}
                  onRemove={onRemoveAttachment}
                />
              )}
            </Stack>
          )}
          <Stack direction="row" alignItems="flex-end">
            {documentFolderOptionEnabled ? (
              <OptionsMenu
                ref={optionsMenuRef}
                items={optionItems}
                icon={<MoreVertIcon />}
                anchorOrigin={{
                  vertical: -MENU_ITEM_HEIGHT * optionItems.length - MENU_PADDING,
                  horizontal: "left",
                }}
                buttonSx={iconButtonSpacing}
              />
            ) : (
              <>
                {fileInputEnabled && (
                  <IconButtonWithTooltip
                    tooltipTitle={`ファイル形式は${allowedExtensions.join(", ")}のみ対応しています`}
                    onClick={() => fileInputRef.current?.click()}
                    icon={
                      <>
                        <AttachFileIcon />
                        <input
                          type="file"
                          hidden
                          accept={allowedExtensions.map(extension => `.${extension}`).join(", ")}
                          multiple
                          ref={fileInputRef}
                          onChange={onFileChange}
                        />
                      </>
                    }
                    iconButtonSx={iconButtonSpacing}
                  />
                )}
              </>
            )}
            <TextField
              fullWidth
              variant="outlined"
              placeholder="何をお手伝いしましょう？"
              size={isTablet ? "small" : "medium"}
              multiline
              maxRows={9.5}
              {...register("question", {
                validate: {
                  notEmpty: value => {
                    const attachmentIds = getValues("attachmentIds");
                    // 添付ファイルまたは質問が必須
                    return attachmentIds?.length !== 0 || value.trim() !== "";
                  },
                },
              })}
              onKeyDown={onEnterPress}
              sx={{
                flex: 1,

                "& .MuiInputBase-root": {
                  px: 0,
                  pl: fileInputEnabled || documentFolderOptionEnabled ? 0 : 2,
                },
                "& .MuiOutlinedInput-notchedOutline": {
                  border: "none",
                },
              }}
            />
            {stoppable ? (
              <IconButton
                onClick={e => {
                  e.preventDefault();
                  onStopChat();
                }}
                sx={iconButtonSpacing}
              >
                <StopCircleOutlinedIcon color="error" />
              </IconButton>
            ) : (
              <IconButton type="submit" disabled={!isValid} sx={iconButtonSpacing}>
                <SendIcon color={!isValid ? "disabled" : "primary"} />
              </IconButton>
            )}
          </Stack>
        </Stack>
      </form>

      <SelectDocumentFolderDialog
        open={isOpenSelectDocumentFolderDialog}
        onClose={closeSelectDocumentFolderDialog}
        documentFolders={documentFolders}
        onSelect={folder => {
          closeSelectDocumentFolderDialog();
          setValue("documentFolder", folder);
        }}
      />
    </>
  );
};
