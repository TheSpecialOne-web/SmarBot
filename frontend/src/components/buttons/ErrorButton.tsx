import { BaseButton, BaseButtonProps } from "./BaseButton";

type Props = Omit<BaseButtonProps, "color">;

export const ErrorButton = (props: Props) => <BaseButton color="error" {...props} />;
