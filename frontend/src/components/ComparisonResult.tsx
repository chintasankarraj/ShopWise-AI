interface Props {
  comparison: any;
}

export default function ComparisonResult({
  comparison,
}: Props) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8">

      <h2 className="text-3xl font-bold">
        🏆 Comparison Result
      </h2>

      <div className="mt-8 overflow-x-auto">

        <table className="w-full">

          <thead>

            <tr className="border-b border-slate-700">

              <th className="py-4 text-left">
                Feature
              </th>

              <th>
                Product A
              </th>

              <th>
                Product B
              </th>

              <th>
                Winner
              </th>

            </tr>

          </thead>

          <tbody>

            {comparison.map((item: any) => (

              <tr
                key={item.feature}
                className="border-b border-slate-800"
              >

                <td className="py-5">
                  {item.feature}
                </td>

                <td>
                  {item.a}
                </td>

                <td>
                  {item.b}
                </td>

                <td className="font-bold text-green-400">
                  {item.winner}
                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </section>
  );
}