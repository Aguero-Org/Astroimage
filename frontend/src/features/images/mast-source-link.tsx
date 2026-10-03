type MastSourceLinkProps = {
  dataUri: string;
};

export function mastFileUrl(dataUri: string): string {
  return `https://mast.stsci.edu/api/v0.1/Download/file?uri=${encodeURIComponent(dataUri)}`;
}

export function MastSourceLink({ dataUri }: Readonly<MastSourceLinkProps>) {
  return (
    <a
      href={mastFileUrl(dataUri)}
      target="_blank"
      rel="noreferrer"
      title={dataUri}
      className="block max-w-56 truncate font-mono text-xs text-primary underline-offset-2 hover:underline dark:text-ring"
      onClick={(event) => event.stopPropagation()}
    >
      {dataUri}
    </a>
  );
}
