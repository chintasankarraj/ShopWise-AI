import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";

export default function LoadingSpinner() {
  return (
    <div className="mx-auto mt-10 max-w-7xl space-y-6 px-6">

      <Skeleton
        height={220}
        borderRadius={24}
        baseColor="#0f172a"
        highlightColor="#1e293b"
      />

      <div className="grid gap-6 lg:grid-cols-2">

        <Skeleton
          height={300}
          borderRadius={24}
          baseColor="#0f172a"
          highlightColor="#1e293b"
        />

        <Skeleton
          height={300}
          borderRadius={24}
          baseColor="#0f172a"
          highlightColor="#1e293b"
        />

      </div>

      <Skeleton
        height={500}
        borderRadius={24}
        baseColor="#0f172a"
        highlightColor="#1e293b"
      />

    </div>
  );
}