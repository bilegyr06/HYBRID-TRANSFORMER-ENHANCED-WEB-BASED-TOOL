import type { SynthesisThemeCluster } from '../../types';

interface ThematicClustersProps {
  clusters?: SynthesisThemeCluster[];
}

export default function ThematicClusters({ clusters }: ThematicClustersProps) {
  if (!clusters?.length) return null;

  return (
    <div>
      <h3 className="text-lg sm:text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-teal-400">*</span> Key Thematic Clusters
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clusters.map((cluster, index) => (
          <div key={`${cluster.title}-${index}`} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-teal-500 transition">
            <h4 className="text-sm sm:text-base font-semibold text-teal-400 mb-2 line-clamp-2">
              {cluster.title}
            </h4>
            <p className="text-sm text-gray-300 mb-3 line-clamp-3">
              {cluster.description}
            </p>
            <div className="flex flex-wrap gap-2">
              {cluster.themes.slice(0, 2).map((theme) => (
                <span key={theme} className="inline-block px-2 py-1 bg-gray-800 rounded text-xs text-gray-300 border border-gray-700">
                  {theme.length > 24 ? `${theme.substring(0, 24)}...` : theme}
                </span>
              ))}
              {cluster.themes.length > 2 && (
                <span className="inline-block px-2 py-1 bg-gray-800 rounded text-xs text-gray-500">
                  +{cluster.themes.length - 2}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
