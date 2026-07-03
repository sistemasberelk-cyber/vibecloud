import { Text } from "@medusajs/ui"
import { getProductPrice } from "@lib/util/get-product-price"
import { HttpTypes } from "@medusajs/types"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import Thumbnail from "../thumbnail"
import PreviewPrice from "./price"

export default async function ProductPreview({
  product,
  isFeatured,
  region,
}: {
  product: HttpTypes.StoreProduct
  isFeatured?: boolean
  region: HttpTypes.StoreRegion
}) {
  const { cheapestPrice } = getProductPrice({
    product,
  })

  return (
    <LocalizedClientLink href={`/products/${product.handle}`} className="group block">
      <div 
        data-testid="product-wrapper" 
        className="p-3 rounded-2xl border border-white/5 bg-zinc-950/20 backdrop-blur-sm transition-all duration-300 hover:border-white/15 hover:shadow-[0_0_20px_rgba(255,255,255,0.03)] hover:-translate-y-1"
      >
        <div className="overflow-hidden rounded-xl bg-zinc-900">
          <div className="transition-transform duration-500 ease-out group-hover:scale-105">
            <Thumbnail
              thumbnail={product.thumbnail}
              images={product.images}
              size="full"
              isFeatured={isFeatured}
            />
          </div>
        </div>
        <div className="flex txt-compact-medium mt-4 justify-between items-center px-1">
          <Text className="text-zinc-400 group-hover:text-white transition-colors duration-200" data-testid="product-title">
            {product.title}
          </Text>
          <div className="flex items-center gap-x-2">
            {cheapestPrice && <PreviewPrice price={cheapestPrice} />}
          </div>
        </div>
      </div>
    </LocalizedClientLink>
  )
}

