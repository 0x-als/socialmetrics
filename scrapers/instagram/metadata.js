import path from "path";
import {fileURLToPath} from "url";
import {HttpsProxyAgent} from "https-proxy-agent";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

process.loadEnvFile(path.join(__dirname, "../../.env"));

const _userAgent = process.env.USER_AGENT;
const _xIgAppId = process.env.X_IG_APP_ID;

if (!_userAgent || !_xIgAppId) {
    console.error("Required headers not found in ENV");
    process.exit(1);
}

const getId = (url) => {
    const regex = /instagram.com\/(?:[A-Za-z0-9_.]+\/)?(p|reels|reel|stories)\/([A-Za-z0-9-_]+)/;
    const match = url.match(regex);
    return match && match[2] ? match[2] : null;
};

const getInstagramGraphqlData = async (url, proxy = null) => {
    const igId = getId(url);
    if (!igId) return {error: "Invalid URL"};

    const graphql = new URL(`https://www.instagram.com/api/graphql`);
    graphql.searchParams.set("variables", JSON.stringify({shortcode: igId}));
    graphql.searchParams.set("doc_id", "10015901848480474");
    graphql.searchParams.set("lsd", "AVqbxe3J_YA");

    const fetchOptions = {
        method: "POST",
        headers: {
            "User-Agent": _userAgent,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-IG-App-ID": _xIgAppId,
            "X-FB-LSD": "AVqbxe3J_YA",
            "X-ASBD-ID": "129477",
            "Sec-Fetch-Site": "same-origin"
        }
    };

    if (proxy) {
        fetchOptions.agent = new HttpsProxyAgent(proxy);
    }

    try {
        const response = await fetch(graphql, fetchOptions);

        if (!response.ok) {
            return {error: `HTTP ${response.status}`};
        }

        const rawText = await response.text();

        try {
            const json = JSON.parse(rawText);
            const items = json?.data?.xdt_shortcode_media;

            return {
                __typename: items?.__typename,
                shortcode: items?.shortcode,
                dimensions: items?.dimensions,
                display_url: items?.display_url,
                display_resources: items?.display_resources,
                has_audio: items?.has_audio,
                video_url: items?.video_url,
                video_view_count: items?.video_view_count,
                video_play_count: items?.video_play_count,
                likes: items?.edge_media_preview_like?.count,
                is_video: items?.is_video,
                caption: items?.edge_media_to_caption?.edges?.[0]?.node?.text,
                is_paid_partnership: items?.is_paid_partnership,
                location: items?.location,
                owner: items?.owner,
                product_type: items?.product_type,
                video_duration: items?.video_duration,
                thumbnail_src: items?.thumbnail_src,
                clips_music_attribution_info: items?.clips_music_attribution_info,
                sidecar: items?.edge_sidecar_to_children?.edges,

                taken_at_timestamp: items?.taken_at_timestamp,

                // ← ДОБАВЛЕНО
                comment_count:
                    items?.edge_media_to_parent_comment?.count ??
                    items?.edge_media_to_comment?.count ??
                    0,


                _raw: json
            };


        } catch {
            return {raw: rawText};
        }

    } catch (err) {
        return {error: err.message};
    }
};

(async () => {
    const url = process.argv[2];
    const proxy = process.argv[3] || null;

    const data = await getInstagramGraphqlData(url, proxy);
    console.log(JSON.stringify(data));
})();