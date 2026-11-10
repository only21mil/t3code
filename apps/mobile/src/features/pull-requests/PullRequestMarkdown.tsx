import {
  splitPullRequestBody,
  type PullRequestBodySegment,
} from "@t3tools/client-runtime/pull-request-markdown";
import { markdownTaskMarkerOffset } from "@t3tools/shared/markdownTaskList";
import type { ReactNode } from "react";
import { View } from "react-native";
import { useProject } from "../../state/entities";
import { pullRequestTarget, type PullRequestParams } from "./usePullRequestDiff";
import {
  PullRequestMedia,
  PullRequestMediaContext,
  usePullRequestMediaUrl,
} from "./PullRequestMedia";
import { videoMimeType } from "@t3tools/shared/video";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import {
  changeRequestReferenceAutolinker,
  resolveChangeRequestMediaUrl,
} from "@t3tools/client-runtime/pull-request-markdown";
import {
  sourceControlClients,
  type ReferenceAutolink,
} from "@t3tools/client-runtime/source-control-clients";
import { SOURCE_CONTROL_MEDIA_ASSET } from "@t3tools/contracts";
import { refreshAssetUrl } from "../../state/assets";
import { usePreparedConnection } from "../../state/session";
import { linkReferenceAutolinks } from "./pullRequestAutolinks";

import { useOpenPullRequest } from "../../native/useOpenPullRequest";
import { SelectableMarkdownText } from "../../native/SelectableMarkdownText";
import { useMarkdownPreviewStyles } from "../files/FileMarkdownPreview";
import { markdownImageSources } from "../../lib/markdownImageSources";
import { FilePreviewGallery, useFilePreviewGallery } from "../../components/ui/FilePreviewGallery";
import { pullRequestImageSource } from "./pullRequestMediaSource";
import {
  FilePreviewModal,
  type FilePreviewSource,
  type FilePreviewItem,
} from "../../components/ui/FilePreviewModal";
import { ThreadMarkdownImageView } from "../threads/ThreadMarkdownImage";
import type {
  MarkdownImageRenderer,
  MarkdownImageSourceResolver,
} from "../../native/SelectableMarkdownText";
import type { SelectableMarkdownTextProps } from "../../native/SelectableMarkdownText.types";

const AutolinksContext = createContext<((text: string) => ReadonlyArray<ReferenceAutolink>) | null>(
  null,
);
const LineBreaksContext = createContext(false);
const MediaRepositoryContext = createContext<{
  readonly provider: string;
  readonly url: string;
} | null>(null);

export function PullRequestMarkdownRepository(props: {
  /** The change request the markdown belongs to, whose host decides what its text links. */
  readonly changeRequest: { readonly provider: string; readonly url: string } | null | undefined;
  readonly params: PullRequestParams;
  readonly children: ReactNode;
}) {
  const provider = props.changeRequest?.provider;
  const url = props.changeRequest?.url;
  const autolinks =
    provider === undefined || url === undefined
      ? null
      : changeRequestReferenceAutolinker({ provider, url });
  const lineBreaks = sourceControlClients.find(provider ?? "")?.hardLineBreaks ?? false;
  const repositoryUrl = url && sourceControlClients.parseChangeRequestUrl(url)?.link.repositoryUrl;
  const mediaRepository = provider && repositoryUrl ? { provider, url: repositoryUrl } : null;
  const target = pullRequestTarget(props.params);
  const project = useProject({
    environmentId: target.environmentId,
    projectId: target.input.projectId,
  });
  const cwd = project?.workspaceRoot;
  const media = cwd
    ? { environmentId: target.environmentId, cwd, repository: target.input.repository }
    : null;
  return (
    <AutolinksContext value={autolinks}>
      <LineBreaksContext value={lineBreaks}>
        <MediaRepositoryContext value={mediaRepository}>
          <PullRequestMediaContext value={media}>{props.children}</PullRequestMediaContext>
        </MediaRepositoryContext>
      </LineBreaksContext>
    </AutolinksContext>
  );
}

/** Images Enriched draws natively, such as one inside a list item, load like the standalone ones. */
function usePullRequestImageSource(resolve: (url: string) => string): MarkdownImageSourceResolver {
  const context = useContext(PullRequestMediaContext);
  const connection = usePreparedConnection(context?.environmentId ?? null);
  const httpBaseUrl = connection._tag === "Some" ? connection.value.httpBaseUrl : null;
  return useCallback(
    async (image) => {
      const url = resolve(image.href);
      const fetchUrl = sourceControlClients.mediaUrl(url)?.fetchUrl;
      if (!fetchUrl) return /^https?:\/\//i.test(url) ? { uri: url } : null;
      // Throwing keeps the image pending until a resolver with its project and connection retries it.
      if (!context || httpBaseUrl === null) throw new Error("Pull request image is unavailable");
      const resource = { _tag: SOURCE_CONTROL_MEDIA_ASSET, cwd: context.cwd, url: fetchUrl };
      const signedUrl = await refreshAssetUrl(context.environmentId, resource);
      if (signedUrl === null) throw new Error("Pull request image is unavailable");
      return { uri: signedUrl };
    },
    [context, httpBaseUrl, resolve],
  );
}

function MarkdownImage(props: {
  readonly href: string;
  readonly alt: string | null;
  readonly onPreview: (source: FilePreviewSource) => void;
}) {
  const media = usePullRequestMediaUrl(props.href);
  const context = useContext(PullRequestMediaContext);
  const withGallery = useFilePreviewGallery();
  return (
    <ThreadMarkdownImageView
      uri={media.uri}
      sourceKey={props.href}
      cacheKey={media.cacheKey}
      unavailable={media.unavailable || !/^https?:\/\//i.test(props.href)}
      alt={props.alt}
      onPressPreview={(source) =>
        props.onPreview(
          withGallery({
            ...pullRequestImageSource(props.href, context),
            name: source.name,
            sourceIdentifier: source.sourceIdentifier,
          }),
        )
      }
    />
  );
}

export function PullRequestMarkdown(props: {
  readonly markdown: string;
  readonly imageGroupMarkdown?: string;
  readonly lineBreaks?: boolean;
  /**
   * `markerOffset` is into `markdown`. Returning false, or a tap that can't be traced back to
   * the source, undoes the tick the renderer already drew.
   */
  readonly onTaskListChange?: (input: {
    readonly markerOffset: number;
    readonly checked: boolean;
  }) => boolean;
}) {
  const mediaContext = useContext(PullRequestMediaContext);
  const mediaRepository = useContext(MediaRepositoryContext);
  const segments = useMemo(() => splitPullRequestBody(props.markdown), [props.markdown]);
  const [undoneTicks, setUndoneTicks] = useState(0);
  const gallery: FilePreviewItem[] = markdownImageSources(
    props.imageGroupMarkdown ?? props.markdown,
  )
    .map((href) => (mediaRepository ? resolveChangeRequestMediaUrl(href, mediaRepository) : href))
    .filter(
      (uri) =>
        /^https?:\/\//i.test(uri) &&
        videoMimeType({ name: uri.split(/[?#]/)[0] ?? uri, mimeType: "" }) === null,
    )
    .map((uri) => pullRequestImageSource(uri, mediaContext));
  const segmentProps = {
    gallery,
    lineBreaks: props.lineBreaks,
    undoneTicks,
    onTaskListChange: props.onTaskListChange,
    onTaskListUndone: () => setUndoneTicks((count) => count + 1),
  };
  return (
    <View style={{ gap: 12 }}>
      {segments.map((segment) => (
        <PullRequestBodySegmentView key={segment.id} segment={segment} {...segmentProps} />
      ))}
    </View>
  );
}

function PullRequestBodySegmentView(props: {
  readonly segment: PullRequestBodySegment;
  readonly gallery: FilePreviewItem[];
  readonly lineBreaks: boolean | undefined;
  readonly undoneTicks: number;
  readonly onTaskListChange:
    | ((input: { readonly markerOffset: number; readonly checked: boolean }) => boolean)
    | undefined;
  readonly onTaskListUndone: () => void;
}) {
  const { segment, onTaskListChange } = props;
  if (segment.kind === "markdown") {
    return (
      <PullRequestMarkdownContent
        key={props.undoneTicks}
        markdown={segment.text}
        gallery={props.gallery}
        lineBreaks={props.lineBreaks}
        onTaskListItemPress={
          onTaskListChange
            ? (event) => {
                const offset = markdownTaskMarkerOffset(
                  segment.text,
                  event.index,
                  event.text,
                  event.checked,
                );
                const kept =
                  offset !== null &&
                  onTaskListChange({
                    markerOffset: segment.sourceOffset + offset,
                    checked: event.checked,
                  });
                if (!kept) props.onTaskListUndone();
              }
            : undefined
        }
      />
    );
  }
  if (segment.kind === "attachment") {
    return <PullRequestMedia url={segment.url} kind={segment.media} />;
  }
  return (
    <View style={{ gap: 12 }}>
      {segment.rows.map((cells, rowIndex) => (
        // oxlint-disable-next-line react/no-array-index-key -- rows have no identity besides position
        <View key={rowIndex} style={{ flexDirection: "row", gap: 12 }}>
          {cells.map((cell, cellIndex) => (
            // oxlint-disable-next-line react/no-array-index-key -- cells have no identity besides position
            <View key={cellIndex} style={{ flex: 1, minWidth: 0, gap: 12 }}>
              {cell.segments.map((cellSegment) => (
                <PullRequestBodySegmentView key={cellSegment.id} {...props} segment={cellSegment} />
              ))}
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}

function PullRequestMarkdownContent(props: {
  readonly markdown: string;
  readonly gallery: FilePreviewItem[];
  readonly lineBreaks: boolean | undefined;
  readonly onTaskListItemPress?: SelectableMarkdownTextProps["onTaskListItemPress"];
}) {
  const hostLineBreaks = useContext(LineBreaksContext);
  const autolinks = useContext(AutolinksContext);
  const mediaContext = useContext(PullRequestMediaContext);
  const mediaRepository = useContext(MediaRepositoryContext);
  const resolveMediaUrl = (href: string) =>
    mediaRepository ? resolveChangeRequestMediaUrl(href, mediaRepository) : href;
  const markdown = linkReferenceAutolinks(props.markdown, autolinks);
  const openPullRequest = useOpenPullRequest();
  const openLink = (href: string) => {
    void openPullRequest(href);
  };
  const [preview, setPreview] = useState<FilePreviewSource | null>(null);
  const renderImage: MarkdownImageRenderer = (image) => (
    <MarkdownImage href={resolveMediaUrl(image.href)} alt={image.alt} onPreview={setPreview} />
  );
  const resolveImageSource = usePullRequestImageSource(resolveMediaUrl);
  const styles = useMarkdownPreviewStyles();
  return (
    <FilePreviewGallery value={props.gallery}>
      <SelectableMarkdownText
        markdown={markdown}
        preserveSoftBreaks={props.lineBreaks ?? hostLineBreaks}
        textStyle={styles.nativeTextStyle}
        onLinkPress={openLink}
        renderImage={renderImage}
        resolveImageSource={resolveImageSource}
        onImagePress={(href) =>
          setPreview(pullRequestImageSource(resolveMediaUrl(href), mediaContext))
        }
        onTaskListItemPress={props.onTaskListItemPress}
      />
      <FilePreviewModal source={preview} onRequestClose={() => setPreview(null)} />
    </FilePreviewGallery>
  );
}
