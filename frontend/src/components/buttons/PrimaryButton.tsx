import { BaseButton, BaseButtonProps } from "./BaseButton";

type Props = Omit<BaseButtonProps, "color">;

export const PrimaryButton = (props: Props) => <BaseButton color="primary" {...props} />;
