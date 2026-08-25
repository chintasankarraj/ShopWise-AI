interface Props {
  message: string;
}

export default function ErrorCard({ message }: Props) {
  return (
    <div className="mx-auto my-8 max-w-3xl rounded-xl border border-red-500/30 bg-red-500/10 p-6">

      <h2 className="text-xl font-semibold text-red-400">
        Something went wrong
      </h2>

      <p className="mt-2 text-gray-300">
        {message}
      </p>

    </div>
  );
}