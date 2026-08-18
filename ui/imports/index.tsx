import svgPaths from "./svg-w6rwu4frs8";
import imgImage from "./e59efe492be663f219c2dd8f5bf13c835d1e95d3.png";
import imgImage1 from "./190655d76eed47a7161394482d3cbd01dc6af439.png";
import imgImage2 from "./0e12f48ec5774600d29003235f18a69ae2cf8845.png";
import imgImage3 from "./ea9eb53fdd7a7b585d6a018f2b8f4c341277dcda.png";
import imgImage4 from "./1978c6d707b6985590abc7345d85c2f8a8558ecc.png";
import imgImage5 from "./52649d9d68983e4081a166a849118649831cbe2c.png";
type IconProps = {
  className?: string;
  property1?: "Add User" | "Book" | "Calendar" | "Calendar Number" | "Coin" | "Command" | "Cube" | "Dollar" | "Icon Down" | "Icon Up" | "Income" | "List" | "Navigation" | "Navigation Right" | "Plus" | "Profile" | "Statistics" | "Target" | "Up" | "User";
};

function Icon({ className, property1 = "User" }: IconProps) {
  const isAddUser = property1 === "Add User";
  const isCalendar = property1 === "Calendar";
  const isCalendarNumber = property1 === "Calendar Number";
  const isCoinOrIconDownOrIconUp = ["Coin", "Icon Down", "Icon Up"].includes(property1);
  const isDollar = property1 === "Dollar";
  const isDollarOrNavigationRight = ["Dollar", "Navigation Right"].includes(property1);
  const isIconUp = property1 === "Icon Up";
  const isIncome = property1 === "Income";
  const isListOrBook = ["List", "Book"].includes(property1);
  const isListOrCalendarOrBook = ["List", "Calendar", "Book"].includes(property1);
  const isNavigation = property1 === "Navigation";
  const isNavigationRight = property1 === "Navigation Right";
  const isNavigationRightOrIncome = ["Navigation Right", "Income"].includes(property1);
  const isPlusOrNavigation = ["Plus", "Navigation"].includes(property1);
  const isProfile = property1 === "Profile";
  const isStatistics = property1 === "Statistics";
  const isTargetOrUp = ["Target", "Up"].includes(property1);
  const isUp = property1 === "Up";
  return (
    <div className={className || "relative size-[24px]"}>
      {["Add User", "Coin", "Icon Down", "Icon Up", "Statistics", "List", "Income", "Calendar Number", "Calendar", "Book"].includes(property1) && (
        <div className={`absolute ${["Calendar Number", "Calendar"].includes(property1) ? "bg-[#cce1ff] inset-[37.5%_6.25%_6.25%_6.25%] rounded-[3px]" : isIncome ? "inset-[0.83%_0_0_0]" : isListOrBook ? "bg-[#cce1ff] inset-[6.25%] rounded-[6px]" : isStatistics ? "bg-[#cce1ff] bottom-[8.33%] left-[8.33%] right-3/4 rounded-[2px] top-1/2" : isCoinOrIconDownOrIconUp ? "inset-[6.25%]" : "bg-[#cce1ff] inset-[56.25%_6.25%_3.13%_6.25%] rounded-bl-[3px] rounded-br-[3px] rounded-tl-[100px] rounded-tr-[100px]"}`}>
          {isCoinOrIconDownOrIconUp && (
            <svg className="absolute block inset-0 size-full" fill="none" height="21" preserveAspectRatio="none" viewBox="0 0 21 21" width="21">
              {["Coin", "Icon Down"].includes(property1) && <circle cx="10.5" cy="10.5" fill="#93BAFB" id="Ellipse 98" r="10.5" />}
              {isIconUp && <path d={svgPaths.p3b81a580} fill="#93BAFB" id="Ellipse 98" />}
            </svg>
          )}
        </div>
      )}
      {["Coin", "Icon Down", "Icon Up", "Statistics", "List", "Income", "Calendar", "Book"].includes(property1) && (
        <div className={`absolute ${isCalendar ? "bg-[#93bafb] inset-[12.5%_6.25%_68.75%_6.25%] rounded-[2px]" : isIncome ? "bg-[#cce1ff] inset-[7.03%_6.25%_6.2%_6.25%] rounded-[6px]" : isListOrBook ? "bg-[#3981f7] bottom-[62.5%] left-[18.75%] right-[43.75%] rounded-[2px] top-1/4" : isStatistics ? "bg-[#3981f7] inset-[31.25%_41.67%_8.33%_41.67%] rounded-[2px]" : "inset-[18.75%]"}`}>
          {isCoinOrIconDownOrIconUp && (
            <svg className="absolute block inset-0 size-full" fill="none" height="15" preserveAspectRatio="none" viewBox="0 0 15 15" width="15">
              <circle cx="7.5" cy="7.5" fill="#CCE1FF" id="Ellipse 99" r="7.5" />
            </svg>
          )}
        </div>
      )}
      {["User", "Profile", "Plus", "Navigation", "Dollar", "Navigation Right", "Target", "Up"].includes(property1) && (
        <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
          <circle cx="12" cy="12" fill={isTargetOrUp ? "#CCE1FF" : isDollarOrNavigationRight ? "#3981F7" : isPlusOrNavigation ? "white" : "#F4F4F5"} id={isTargetOrUp ? "Ellipse 457" : isDollarOrNavigationRight ? "Ellipse 98" : isPlusOrNavigation ? "Ellipse 118" : "Ellipse 448"} r="12" />
        </svg>
      )}
      {["Plus", "Navigation", "Calendar Number", "Up"].includes(property1) && (
        <div className={`absolute ${isUp ? "inset-[16.67%_16.84%_16.67%_16.49%]" : isCalendarNumber ? "bottom-[18.75%] left-[34.38%] right-[34.38%] top-1/2" : "inset-[10%]"}`} data-name="Frame">
          <svg className="absolute block inset-0 size-full" fill="none" height={isUp ? "16" : isCalendarNumber ? "7.5" : "19.2"} preserveAspectRatio="none" viewBox={isUp ? "0 0 16 16" : isCalendarNumber ? "0 0 7.5 7.5" : "0 0 19.2 19.2"} width={isUp ? "16" : isCalendarNumber ? "7.5" : "19.2"}>
            <g clipPath={isUp ? "url(#clip0_0_829)" : isCalendarNumber ? "url(#clip0_0_857)" : isNavigation ? "url(#clip0_0_851)" : "url(#clip0_0_749)"} id="Frame">
              <g id="Vector" />
              <path d={isUp ? svgPaths.p30902000 : isCalendarNumber ? "M4.0625 6.25V1.25L2.5 2.8125" : isNavigation ? "M4 9.6H15.2" : "M9.6 4V15.2"} id="Vector_2" stroke="#3981F7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={isCalendarNumber ? "2" : "1.5"} />
              {["Plus", "Navigation", "Up"].includes(property1) && <path d={isUp ? "M9.33333 4.66667H14V9.33333" : isNavigation ? "M12 12.8L15.2 9.6" : "M4 9.6H15.2"} id="Vector_3" stroke="#3981F7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />}
              {isNavigation && <path d="M12 6.4L15.2 9.6" id="Vector_4" stroke="#3981F7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />}
            </g>
            <defs>
              <clipPath id={isUp ? "clip0_0_829" : isCalendarNumber ? "clip0_0_857" : isNavigation ? "clip0_0_851" : "clip0_0_749"}>
                <rect fill="white" height={isUp ? "16" : isCalendarNumber ? "7.5" : "19.2"} width={isUp ? "16" : isCalendarNumber ? "7.5" : "19.2"} />
              </clipPath>
            </defs>
          </svg>
        </div>
      )}
      {["Statistics", "List", "Calendar", "Book"].includes(property1) && <div className={`absolute rounded-[2px] ${isCalendar ? "bg-white inset-[3.13%_68.75%_78.13%_21.88%]" : isListOrBook ? "bg-[#93bafb] bottom-[40.63%] left-[18.75%] right-[18.75%] top-1/2" : "bg-[#93bafb] bottom-[8.33%] left-3/4 right-[8.33%] top-[8.33%]"}`} />}
      {isListOrCalendarOrBook && (
        <>
          <div className={`absolute rounded-[2px] ${isCalendar ? "bg-white inset-[3.13%_21.88%_78.13%_68.75%]" : "bg-[#93bafb] inset-[71.88%_62.5%_18.75%_18.75%]"}`} />
          <div className={`absolute ${isCalendar ? "bg-[#3981f7] inset-[62.5%_62.5%_18.75%_18.75%] rounded-[1px]" : "bg-[#93bafb] inset-[71.88%_18.75%_18.75%_43.75%] rounded-[2px]"}`} />
        </>
      )}
      {["Coin", "Dollar"].includes(property1) && (
        <div className={`absolute ${isDollar ? "inset-1/4" : "inset-[31.25%]"}`} data-name="emojione-v1:heavy-dollar-sign">
          <svg className="absolute block inset-0 size-full" fill="none" height={isDollar ? "12" : "9"} preserveAspectRatio="none" viewBox={isDollar ? "0 0 12 12" : "0 0 9 9"} width={isDollar ? "12" : "9"}>
            <g clipPath={isDollar ? "url(#clip0_0_723)" : "url(#clip0_0_867)"} id="emojione-v1:heavy-dollar-sign">
              <path d={isDollar ? svgPaths.p21299ba0 : svgPaths.p24436b40} fill={isDollar ? "#EBF3FF" : "#3981F7"} id="Vector" />
            </g>
            <defs>
              <clipPath id={isDollar ? "clip0_0_723" : "clip0_0_867"}>
                <rect fill="white" height={isDollar ? "12" : "9"} width={isDollar ? "12" : "9"} />
              </clipPath>
            </defs>
          </svg>
        </div>
      )}
      {["Icon Down", "Icon Up"].includes(property1) && (
        <div className="absolute inset-[31.25%]" data-name="Icon">
          <svg className="absolute block inset-0 size-full" fill="none" height="9" preserveAspectRatio="none" viewBox="0 0 9 9" width="9">
            <g id="Icon">
              <path d={isIconUp ? "M7.5 6L4.5 3L1.5 6" : "M1.5 3L4.5 6L7.5 3"} fill="#3981F7" id="Vector" stroke="#3981F7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </g>
          </svg>
        </div>
      )}
      {isNavigationRightOrIncome && (
        <>
          <div className={`absolute ${isIncome ? "inset-[0_30%_80.17%_30%]" : "inset-[10%]"}`} data-name="Vector">
            <svg className="absolute block inset-0 size-full" fill="none" height={isIncome ? "4.76025" : "32"} preserveAspectRatio="none" viewBox={isIncome ? "0 0 9.6 4.76025" : "0 0 32 32"} width={isIncome ? "9.6" : "32"}>
              {isNavigationRight && <g id="Vector" />}
              {isIncome && <path d={svgPaths.p21cf2900} fill="#93BAFB" id="Vector" />}
            </svg>
          </div>
          <div className={`absolute ${isIncome ? "inset-[50.42%_62.5%_19.83%_18.75%]" : "bottom-1/2 left-[26.67%] right-[26.67%] top-1/2"}`} data-name="Vector">
            {isNavigationRight && (
              <div className="absolute inset-[-0.75px_-6.7%]">
                <svg className="block size-full" fill="none" height="1.5" preserveAspectRatio="none" viewBox="0 0 12.7 1.5" width="12.7">
                  <path d="M0.75 0.75H11.95" id="Vector" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                </svg>
              </div>
            )}
            {isIncome && (
              <svg className="absolute block inset-0 size-full" fill="none" height="7.14038" preserveAspectRatio="none" viewBox="0 0 4.5 7.14038" width="4.5">
                <path d={svgPaths.p5c9f540} fill="#3981F7" id="Vector" />
              </svg>
            )}
          </div>
        </>
      )}
      {property1 === "Cube" && (
        <div className="absolute contents inset-0" data-name="vuesax/bold/3dcube">
          <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
            <g id="3dcube">
              <path d={svgPaths.p352fd8c0} fill="#3981F7" id="Vector" />
              <path d={svgPaths.p17d66200} fill="#93BAFB" id="Vector_2" />
              <path d={svgPaths.p2d905100} fill="#CCE1FF" id="Vector_3" />
              <g id="Vector_4" opacity="0" />
            </g>
          </svg>
        </div>
      )}
      {isAddUser && (
        <div className="absolute inset-[56.25%_31.25%_6.25%_31.25%]" data-name="mdi:tie">
          <svg className="absolute block inset-0 size-full" fill="none" height="9" preserveAspectRatio="none" viewBox="0 0 9 9" width="9">
            <g id="mdi:tie">
              <path d={svgPaths.p8838380} fill="#3981F7" id="Vector" />
            </g>
          </svg>
        </div>
      )}
      {["Add User", "Calendar Number"].includes(property1) && (
        <div className={`absolute ${isCalendarNumber ? "bg-[#93bafb] inset-[12.5%_6.25%_68.75%_6.25%] rounded-[2px]" : "bottom-1/2 left-[28.13%] right-[28.13%] top-[6.25%]"}`}>
          {isAddUser && (
            <svg className="absolute block inset-0 size-full" fill="none" height="10.5" preserveAspectRatio="none" viewBox="0 0 10.5 10.5" width="10.5">
              <circle cx="5.25" cy="5.25" fill="#93BAFB" id="Ellipse 458" r="5.25" />
            </svg>
          )}
        </div>
      )}
      {["Add User", "Income", "Calendar Number"].includes(property1) && (
        <div className={`absolute ${isCalendarNumber ? "bg-white inset-[3.13%_68.75%_78.13%_21.88%] rounded-[2px]" : isIncome ? "bg-[#93bafb] inset-[67.77%_18.75%_22.93%_46.25%] rounded-[2px]" : "contents inset-[18.75%_40.63%_62.5%_40.63%]"}`}>
          {isAddUser && (
            <>
              <div className="absolute bg-white inset-[18.75%_46.88%_62.5%_46.88%] rounded-[2px]" />
              <div className="absolute bottom-[68.75%] flex items-center justify-center left-[40.62%] right-[40.62%] top-1/4" style={{ containerType: "size" }}>
                <div className="-rotate-90 flex-none h-[100cqw] w-[100cqh]">
                  <div className="bg-white relative rounded-[2px] size-full" />
                </div>
              </div>
            </>
          )}
        </div>
      )}
      {property1 === "User" && (
        <div className="absolute contents inset-1/4" data-name="vuesax/bold/user">
          <div className="absolute inset-1/4" data-name="user">
            <svg className="absolute block inset-0 size-full" fill="none" height="12" preserveAspectRatio="none" viewBox="0 0 12 12" width="12">
              <g id="user">
                <g id="Vector" opacity="0" />
                <path d={svgPaths.p868be70} fill="#9096A2" id="Vector_2" />
                <path d={svgPaths.p1f5b4b00} fill="#9096A2" id="Vector_3" />
              </g>
            </svg>
          </div>
        </div>
      )}
      {isProfile && (
        <>
          <div className="absolute contents inset-1/4" style={{ containerType: "size" }} data-name="vuesax/linear/document-text">
            <div className="absolute flex inset-1/4 items-center justify-center" style={{ containerType: "size" }}>
              <div className="-rotate-90 flex-none h-[100cqw] w-[100cqh]">
                <div className="relative size-full" data-name="document-text">
                  <svg className="absolute block inset-0 size-full" fill="none" height="12" preserveAspectRatio="none" viewBox="0 0 12 12" width="12">
                    <g id="document-text">
                      <path d={svgPaths.p3afc8d00} fill="#9096A2" id="Vector" />
                      <g id="Vector_2" opacity="0" />
                    </g>
                  </svg>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute contents inset-[35%]" data-name="vuesax/bold/user-octagon">
            <div className="absolute inset-[35%]" data-name="user-octagon">
              <svg className="absolute block inset-0 size-full" fill="none" height="7.2" preserveAspectRatio="none" viewBox="0 0 7.2 7.2" width="7.2">
                <g id="user-octagon">
                  <g id="Vector" opacity="0" />
                  <path d={svgPaths.p3ee6280} fill="#F4F4F5" id="Vector_2" />
                </g>
              </svg>
            </div>
          </div>
        </>
      )}
      {isNavigationRight && (
        <>
          <div className="absolute bottom-[36.67%] left-[60%] right-[26.67%] top-1/2" data-name="Vector">
            <div className="absolute inset-[-23.44%]">
              <svg className="block size-full" fill="none" height="4.7" preserveAspectRatio="none" viewBox="0 0 4.7 4.7" width="4.7">
                <path d="M0.75 3.95L3.95 0.75" id="Vector" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
          <div className="absolute bottom-1/2 left-[60%] right-[26.67%] top-[36.67%]" data-name="Vector">
            <div className="absolute inset-[-23.44%]">
              <svg className="block size-full" fill="none" height="4.7" preserveAspectRatio="none" viewBox="0 0 4.7 4.7" width="4.7">
                <path d="M0.75 0.75L3.95 3.95" id="Vector" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </>
      )}
      {property1 === "Target" && (
        <div className="absolute inset-[16.48%_23.52%_23.52%_23.15%]" data-name="Group">
          <div className="absolute inset-[-13.89%_-15.62%]">
            <svg className="block size-full" fill="none" height="18.4" preserveAspectRatio="none" viewBox="0 0 16.8 18.4" width="16.8">
              <g id="Group">
                <path d={svgPaths.p21bdbe00} id="Vector" stroke="#93BAFB" strokeLinejoin="round" strokeMiterlimit="2" strokeWidth="4" />
                <path d={svgPaths.p125a6700} fill="#3981F7" id="Vector_2" />
                <path d={svgPaths.p7d8d1f0} fill="#93BAFB" id="Vector_3" />
                <path d="M8.40001 3.6V2" id="Vector_4" stroke="#93BAFB" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="2" strokeWidth="4" />
              </g>
            </svg>
          </div>
        </div>
      )}
      {isCalendarNumber && <div className="absolute bg-white inset-[3.13%_21.88%_78.13%_68.75%] rounded-[2px]" />}
      {property1 === "Command" && (
        <div className="absolute contents inset-0" data-name="vuesax/bold/command">
          <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
            <g id="command">
              <g id="Vector" opacity="0" />
              <path d="M16 8H8V16H16V8Z" fill="#3981F7" id="Vector_2" />
              <path d={svgPaths.p1a02e300} fill="#93BAFB" id="Vector_3" />
              <path d={svgPaths.p1ec8400} fill="#CCE1FF" id="Vector_4" />
              <path d={svgPaths.p321c7200} fill="#93BAFB" id="Vector_5" />
              <path d={svgPaths.p2d042540} fill="#CCE1FF" id="Vector_6" />
            </g>
          </svg>
        </div>
      )}
    </div>
  );
}

function Label({ className }: { className?: string }) {
  return (
    <div className={className || "bg-[#ceefdf] relative rounded-[100px]"} data-name="Label">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[8px] items-center px-[12px] py-[10px] relative size-full">
          <div className="relative shrink-0 size-[20px]" data-name="Frame">
            <svg className="absolute block inset-0 size-full" fill="none" height="20" preserveAspectRatio="none" viewBox="0 0 20 20" width="20">
              <g clipPath="url(#clip0_0_736)" id="Frame">
                <g id="Vector" />
                <path d={svgPaths.p3551b880} id="Vector_2" stroke="#0AAF60" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
              </g>
              <defs>
                <clipPath id="clip0_0_736">
                  <rect fill="white" height="20" width="20" />
                </clipPath>
              </defs>
            </svg>
          </div>
          <p className="[word-break:break-word] font-['TT_Hoves:DemiBold',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0aaf60] text-[14px] whitespace-nowrap">Connected</p>
        </div>
      </div>
    </div>
  );
}
type AvatarProps = {
  className?: string;
  showCheck?: boolean;
  size?: "40px" | "48px";
  type?: "Memoji" | "Real Photo";
};

function Avatar({ className, showCheck = true, size = "40px", type = "Real Photo" }: AvatarProps) {
  const isMemojiAnd48Px = type === "Memoji" && size === "48px";
  return (
    <div className={className || `relative ${isMemojiAnd48Px ? "size-[48px]" : "rounded-[100px]"}`}>
      {type === "Real Photo" && size === "40px" && (
        <div className="content-stretch flex items-start relative size-full">
          <div className="relative rounded-[100px] shrink-0 size-[40px]" data-name="Image">
            <div aria-hidden className="absolute inset-0 pointer-events-none rounded-[100px]">
              <div className="absolute bg-[#a9b58d] inset-0 rounded-[100px]" />
              <img alt="" className="absolute max-w-none object-cover rounded-[100px] size-full" src={imgImage} />
            </div>
          </div>
          {showCheck && (
            <div className="absolute inset-[60%_0_0_60%]" data-name="Check">
              <svg className="absolute block inset-0 size-full" fill="none" height="16" preserveAspectRatio="none" viewBox="0 0 16 16" width="16">
                <g id="Check">
                  <circle cx="8" cy="8" fill="#3981F7" id="Ellipse 129" r="8" />
                  <g clipPath="url(#clip0_0_798)" id="Frame">
                    <g id="Vector" />
                    <path d={svgPaths.p1ba6d000} id="Vector_2" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                  </g>
                </g>
                <defs>
                  <clipPath id="clip0_0_798">
                    <rect fill="white" height="8" transform="translate(4.00002 3.9999)" width="8" />
                  </clipPath>
                </defs>
              </svg>
            </div>
          )}
        </div>
      )}
      {isMemojiAnd48Px && (
        <>
          <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
            <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
          </svg>
          <div className="absolute inset-[8.33%]" data-name="Image">
            <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage1} />
          </div>
        </>
      )}
      {isMemojiAnd48Px && showCheck && (
        <div className="absolute inset-[66.67%_0_0_66.67%]" data-name="Check">
          <svg className="absolute block inset-0 size-full" fill="none" height="16" preserveAspectRatio="none" viewBox="0 0 16 16" width="16">
            <g id="Check">
              <circle cx="8" cy="8" fill="#3981F7" id="Ellipse 129" r="8" />
              <g clipPath="url(#clip0_0_780)" id="Frame">
                <g id="Vector" />
                <path d={svgPaths.p1ba6d000} id="Vector_2" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
              </g>
            </g>
            <defs>
              <clipPath id="clip0_0_780">
                <rect fill="white" height="8" transform="translate(4.00002 3.9999)" width="8" />
              </clipPath>
            </defs>
          </svg>
        </div>
      )}
    </div>
  );
}
type NavbarProps = {
  className?: string;
  heading?: string;
  property1?: "Default";
  showBradcrumbs?: boolean;
  showButton?: boolean;
  showSub?: boolean;
  subHeading?: string;
};

function Navbar({ className, heading = "Good morning, Chris", property1 = "Default", showBradcrumbs = false, showButton = true, showSub = true, subHeading = "Here’s your dashboard overview." }: NavbarProps) {
  return (
    <div className={className || "relative w-[1160px]"}>
      <div className="content-stretch flex gap-[120px] items-start px-[32px] py-[24px] relative size-full">
        <div className="content-stretch flex flex-[1_0_0] flex-col gap-[4px] items-start min-w-px relative" data-name="Title">
          <p className="[word-break:break-word] font-['TT_Hoves:DemiBold',sans-serif] leading-[1.5] not-italic relative shrink-0 text-[#0a112f] text-[32px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
            {heading}
          </p>
          {showSub && (
            <p className="[word-break:break-word] font-['TT_Hoves:Regular',sans-serif] leading-[1.6] min-w-full not-italic relative shrink-0 text-[#585860] text-[16px] w-[min-content]" style={{ fontFeatureSettings: '"ss03" 1' }}>
              {subHeading}
            </p>
          )}
          {showBradcrumbs && (
            <div className="relative shrink-0" data-name="Breadcrumbs">
              <div className="flex flex-row items-center size-full">
                <div className="content-stretch flex gap-[8px] items-center relative size-full">
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                    Contract
                  </p>
                  <div className="overflow-clip relative shrink-0 size-[16px]" data-name="Icon">
                    <svg className="absolute block inset-0 size-full" fill="none" height="32" preserveAspectRatio="none" viewBox="0 0 32 32" width="32">
                      <g id="Vector" />
                    </svg>
                    <div className="absolute bottom-1/4 left-[37.5%] right-[37.5%] top-1/4" data-name="Vector">
                      <div className="absolute inset-[-9.38%_-18.75%]">
                        <svg className="block size-full" fill="none" height="9.5" preserveAspectRatio="none" viewBox="0 0 5.5 9.5" width="5.5">
                          <path d={svgPaths.p2fd49480} id="Vector" stroke="#0A112F" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                    General Info
                  </p>
                  <div className="overflow-clip relative shrink-0 size-[16px]" data-name="Icon">
                    <svg className="absolute block inset-0 size-full" fill="none" height="32" preserveAspectRatio="none" viewBox="0 0 32 32" width="32">
                      <g id="Vector" />
                    </svg>
                    <div className="absolute bottom-1/4 left-[37.5%] right-[37.5%] top-1/4" data-name="Vector">
                      <div className="absolute inset-[-9.38%_-18.75%]">
                        <svg className="block size-full" fill="none" height="9.5" preserveAspectRatio="none" viewBox="0 0 5.5 9.5" width="5.5">
                          <path d={svgPaths.p2fd49480} id="Vector" stroke="#0A112F" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                    Scope of Work
                  </p>
                  <div className="overflow-clip relative shrink-0 size-[16px]" data-name="Icon">
                    <svg className="absolute block inset-0 size-full" fill="none" height="32" preserveAspectRatio="none" viewBox="0 0 32 32" width="32">
                      <g id="Vector" />
                    </svg>
                    <div className="absolute bottom-1/4 left-[37.5%] right-[37.5%] top-1/4" data-name="Vector">
                      <div className="absolute inset-[-9.38%_-18.75%]">
                        <svg className="block size-full" fill="none" height="9.5" preserveAspectRatio="none" viewBox="0 0 5.5 9.5" width="5.5">
                          <path d={svgPaths.p2fd49480} id="Vector" stroke="#0A112F" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                    Payment Details
                  </p>
                  <div className="overflow-clip relative shrink-0 size-[16px]" data-name="Icon">
                    <svg className="absolute block inset-0 size-full" fill="none" height="32" preserveAspectRatio="none" viewBox="0 0 32 32" width="32">
                      <g id="Vector" />
                    </svg>
                    <div className="absolute bottom-1/4 left-[37.5%] right-[37.5%] top-1/4" data-name="Vector">
                      <div className="absolute inset-[-9.38%_-18.75%]">
                        <svg className="block size-full" fill="none" height="9.5" preserveAspectRatio="none" viewBox="0 0 5.5 9.5" width="5.5">
                          <path d={svgPaths.p2fd49480} id="Vector" stroke="#0A112F" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                    Sign
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="content-stretch flex gap-[20px] items-center justify-end relative shrink-0" data-name="Right Menu">
          {showButton && (
            <div className="bg-[#3981f7] relative rounded-[100px] shrink-0" data-name="Button">
              <div className="flex flex-row items-center justify-center size-full">
                <div className="content-stretch flex gap-[12px] items-center justify-center px-[20px] py-[10px] relative size-full">
                  <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.4] not-italic relative shrink-0 text-[14px] text-white tracking-[-0.14px] whitespace-nowrap">Create A Contract</p>
                  <Icon className="relative shrink-0 size-[24px]" property1="Plus" />
                </div>
              </div>
            </div>
          )}
          <div className="content-stretch flex items-start p-[8px] relative shrink-0" data-name="Icon">
            <div className="relative shrink-0 size-[24px]" data-name="Icon">
              <div className="absolute contents inset-0" data-name="vuesax/bold/notification">
                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                  <g id="notification">
                    <path d={svgPaths.pcd71700} fill="#9096A2" id="Vector" />
                    <path d={svgPaths.p144aa1f0} fill="#9096A2" id="Vector_2" />
                    <g id="Vector_3" opacity="0" />
                  </g>
                </svg>
              </div>
            </div>
          </div>
          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="User">
            <Avatar className="relative rounded-[100px] shrink-0" showCheck={false} />
            <div className="[word-break:break-word] content-stretch flex flex-col gap-px items-start leading-[1.6] not-italic relative shrink-0 whitespace-nowrap" data-name="Text">
              <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[14px]">Chris Miguel</p>
              <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[12px] tracking-[0.12px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
                Freelancer
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Sidebar({ className }: { className?: string }) {
  return (
    <div className={className || "bg-white h-[850px] relative w-[280px]"} data-name="Sidebar">
      <div aria-hidden className="absolute border-[#e4e4e7] border-r border-solid inset-0 pointer-events-none" />
      <div className="content-stretch flex flex-col items-start relative size-full">
        <div className="content-stretch flex flex-[1_0_0] flex-col items-center min-h-px relative w-[279px]" data-name="Menu">
          <div className="flex-[1_0_0] min-h-px relative w-full" data-name="Leading content">
            <div className="flex flex-col items-center size-full">
              <div className="content-stretch flex flex-col gap-[56px] items-center py-[32px] relative size-full">
                <div className="relative shrink-0 w-full" data-name="Header">
                  <div className="content-stretch flex flex-col items-start pl-[32px] pr-[24px] relative size-full">
                    <div className="content-stretch flex gap-[8px] items-center relative shrink-0" data-name="Logo">
                      <div className="relative shrink-0 size-[24px]" data-name="Mask group">
                        <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                          <g id="Mask group">
                            <mask height="24" id="mask0_0_754" maskUnits="userSpaceOnUse" style={{ maskType: "alpha" }} width="24" x="0" y="0">
                              <circle cx="12" cy="12" fill="#C4C4C4" id="Ellipse 443" r="12" />
                            </mask>
                            <g mask="url(#mask0_0_754)">
                              <g id="Group 39786">
                                <circle cx="6.29216" cy="-2.13104" fill="#0A112F" id="Ellipse 444" r="9.9559" transform="rotate(-22 6.29216 -2.13104)" />
                                <circle cx="17.711" cy="26.1308" fill="#0A112F" id="Ellipse 445" r="9.9559" transform="rotate(-22 17.711 26.1308)" />
                                <circle cx="-2.12892" cy="17.7093" fill="#0A112F" id="Ellipse 446" r="9.9559" transform="rotate(-22 -2.12892 17.7093)" />
                                <circle cx="25.8706" cy="5.64347" fill="#0A112F" id="Ellipse 447" r="9.9559" transform="rotate(-22 25.8706 5.64347)" />
                              </g>
                            </g>
                          </g>
                        </svg>
                      </div>
                      <div className="[word-break:break-word] flex flex-col font-['Satoshi:Bold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#0a112f] text-[24px] tracking-[-0.48px] whitespace-nowrap">
                        <p className="leading-[32px]">Payrole</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="relative shrink-0 w-full" data-name="Navigation">
                  <div className="content-stretch flex flex-col gap-[16px] items-start pl-[24px] pr-[16px] relative size-full">
                    <div className="bg-[#fafafa] relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[12px]" />
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=home">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/home-2">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="home-2">
                                    <path d={svgPaths.p37a1e000} fill="#3981F7" id="Vector" />
                                    <g id="Vector_2" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#3981f7] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Home
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=edit">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/edit-2">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="edit-2">
                                    <path d={svgPaths.p3dd95700} fill="#9096A2" id="Vector" />
                                    <path d={svgPaths.p33964d80} fill="#9096A2" id="Vector_2" />
                                    <g id="Vector_3">
                                      <path d={svgPaths.p3ca4c700} fill="#9096A2" />
                                    </g>
                                    <g id="Vector_4" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Contracts
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=document">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/document-text">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="document-text">
                                    <path d={svgPaths.p25442900} fill="#9096A2" id="Vector" />
                                    <path d={svgPaths.p64d0a80} fill="#9096A2" id="Vector_2" />
                                    <g id="Vector_3" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Documents
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=notes">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/document-normal">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="document-normal">
                                    <path d={svgPaths.pe3ce200} fill="#9096A2" id="Vector" />
                                    <path d={svgPaths.p1985c800} fill="#9096A2" id="Vector_2" />
                                    <g id="Vector_3" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                              <div className="absolute inset-[40%_37.5%_20%_37.5%]" data-name="Vector">
                                <svg className="absolute block inset-0 size-full" fill="none" height="9.6" preserveAspectRatio="none" viewBox="0 0 6 9.6" width="6">
                                  <path d={svgPaths.p20b07040} fill="white" id="Vector" />
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Invoices
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=transaction">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/convert-card">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="convert-card">
                                    <path d="M24 0H0V24H24V0Z" fill="#9096A2" id="Vector" opacity="0" />
                                    <path d={svgPaths.pa2a4c80} id="Vector_2" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                                    <path d={svgPaths.p80a24a0} id="Vector_3" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                                    <path d={svgPaths.p3f12eb00} fill="#9096A2" id="Vector_4" />
                                    <path d={svgPaths.p2f18ed00} fill="#9096A2" id="Vector_5" />
                                    <path d={svgPaths.p1e13e500} fill="#9096A2" id="Vector_6" />
                                    <path d={svgPaths.p2fb99900} fill="#9096A2" id="Vector_7" />
                                  </g>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Transactions
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=secure">
                              <div className="absolute contents inset-0" data-name="vuesax/linear/security">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="security">
                                    <path d={svgPaths.p1afc8970} fill="#9096A2" id="Vector" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                                    <g id="Vector_2" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                              <div className="absolute left-[6px] size-[12px] top-[6px]" data-name="Frame">
                                <svg className="absolute block inset-0 size-full" fill="none" height="12" preserveAspectRatio="none" viewBox="0 0 12 12" width="12">
                                  <g clipPath="url(#clip0_0_804)" id="Frame">
                                    <g id="Vector" />
                                    <path d={svgPaths.p1b2f5c00} id="Vector_2" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
                                  </g>
                                  <defs>
                                    <clipPath id="clip0_0_804">
                                      <rect fill="white" height="12" width="12" />
                                    </clipPath>
                                  </defs>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Insurance
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative rounded-[12px] shrink-0 w-[231px]" data-name="Vertical Navigation">
                      <div className="flex flex-row items-center size-full">
                        <div className="content-stretch flex items-center p-[12px] relative size-full">
                          <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                            <div className="relative shrink-0 size-[24px]" data-name="Property 1=card">
                              <div className="absolute contents inset-0" data-name="vuesax/bold/card">
                                <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                  <g id="card">
                                    <path d={svgPaths.p347d0e00} fill="#9096A2" id="Vector" />
                                    <path d={svgPaths.p2d7b2a40} fill="#9096A2" id="Vector_2" />
                                    <g id="Vector_3" opacity="0" />
                                  </g>
                                </svg>
                              </div>
                            </div>
                            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                              Cards
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex-[1_0_0] min-h-px relative w-full" data-name="Navigation">
                  <div className="flex flex-col justify-end size-full">
                    <div className="content-stretch flex flex-col items-start justify-end px-[16px] relative size-full">
                      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Vertical Navigation">
                        <div className="flex flex-row items-center size-full">
                          <div className="content-stretch flex items-center p-[12px] relative size-full">
                            <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Content">
                              <div className="relative shrink-0 size-[24px]" data-name="Property 1=settings">
                                <div className="absolute contents inset-0" data-name="vuesax/bold/setting-2">
                                  <svg className="absolute block inset-0 size-full" fill="none" height="24" preserveAspectRatio="none" viewBox="0 0 24 24" width="24">
                                    <g id="setting-2">
                                      <path d={svgPaths.p3f496a00} fill="#9096A2" id="Vector" />
                                      <g id="Vector_2" opacity="0" />
                                    </g>
                                  </svg>
                                </div>
                              </div>
                              <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#9096a2] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
                                Settings
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Title() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0" data-name="Title">
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Total Outstanding
      </p>
    </div>
  );
}

function Content2() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[14px] items-start min-w-px relative" data-name="Content">
      <Title />
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[0] not-italic relative shrink-0 text-[#0a112f] text-[0px] tracking-[-0.4px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        <span className="leading-[1.3] text-[32px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
          $58,764
        </span>
        <span className="leading-[1.4] text-[#9096a2] text-[24px] tracking-[-0.24px]">.25</span>
      </p>
    </div>
  );
}

function Content1() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[16px] items-start min-w-px relative" data-name="Content">
      <Icon className="relative shrink-0 size-[24px]" property1="Statistics" />
      <Content2 />
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Upcoming Payment
      </p>
    </div>
  );
}

function Text() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[14px] items-start min-w-px relative" data-name="Text">
      <Frame />
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[0] not-italic relative shrink-0 text-[#0a112f] text-[0px] tracking-[-0.4px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        <span className="leading-[1.3] text-[32px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
          April 1st
        </span>
        <span className="leading-[1.4] text-[#9096a2] text-[24px] tracking-[-0.24px]">, 2022</span>
      </p>
    </div>
  );
}

function Content3() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[16px] items-start min-w-px relative" data-name="Content">
      <Icon className="relative shrink-0 size-[24px]" property1="Calendar" />
      <Text />
    </div>
  );
}

function Content() {
  return (
    <div className="content-stretch flex gap-[40px] items-start relative shrink-0 w-full" data-name="Content">
      <Content1 />
      <div className="flex items-center justify-center relative self-stretch shrink-0 w-0" style={{ containerType: "size" }}>
        <div className="flex-none rotate-90 w-[100cqh]">
          <div className="h-0 relative w-full" data-name="Divider">
            <div className="absolute inset-[-1px_0_0_0]">
              <svg className="block size-full" fill="none" height="1" preserveAspectRatio="none" viewBox="0 0 82 1" width="82">
                <line id="Divider" stroke="#F4F4F5" x2="82" y1="0.5" y2="0.5" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      <Content3 />
    </div>
  );
}

function Card() {
  return (
    <div className="content-stretch flex flex-col items-start p-[24px] relative rounded-[16px] shrink-0 w-[626px]" data-name="Card #1">
      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[16px]" />
      <Content />
    </div>
  );
}

function Title1() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full" data-name="Title">
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Withdraw Method
      </p>
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icon">
        <svg className="absolute block inset-0 size-full" fill="none" height="32" preserveAspectRatio="none" viewBox="0 0 32 32" width="32">
          <g id="Vector" />
        </svg>
        <div className="absolute bottom-[45.83%] left-[16.67%] right-3/4 top-[45.83%]" data-name="Vector">
          <div className="absolute inset-[-37.5%]">
            <svg className="block size-full" fill="none" height="3.5" preserveAspectRatio="none" viewBox="0 0 3.5 3.5" width="3.5">
              <path d={svgPaths.p1013cd00} fill="#0A112F" id="Vector" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-[45.83%]" data-name="Vector">
          <div className="absolute inset-[-37.5%]">
            <svg className="block size-full" fill="none" height="3.5" preserveAspectRatio="none" viewBox="0 0 3.5 3.5" width="3.5">
              <path d={svgPaths.p1013cd00} fill="#0A112F" id="Vector" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
            </svg>
          </div>
        </div>
        <div className="absolute bottom-[45.83%] left-3/4 right-[16.67%] top-[45.83%]" data-name="Vector">
          <div className="absolute inset-[-37.5%]">
            <svg className="block size-full" fill="none" height="3.5" preserveAspectRatio="none" viewBox="0 0 3.5 3.5" width="3.5">
              <path d={svgPaths.p1013cd00} fill="#0A112F" id="Vector" stroke="#9096A2" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function PayPal() {
  return (
    <div className="absolute inset-[20%]" data-name="PayPal">
      <svg className="absolute block inset-0 size-full" fill="none" height="28.8" preserveAspectRatio="none" viewBox="0 0 28.8 28.8" width="28.8">
        <g id="PayPal">
          <path d={svgPaths.p1a1a2980} fill="#253B80" id="Vector" />
          <path d={svgPaths.p3ad15500} fill="#222D65" id="Vector_2" />
          <path d={svgPaths.p7e2ee00} fill="#253B80" id="Vector_3" />
          <path d={svgPaths.pacc6180} fill="#179BD7" id="Vector_4" />
        </g>
      </svg>
    </div>
  );
}

function Nasdaq() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-start leading-[1.6] not-italic relative shrink-0 whitespace-nowrap" data-name="Nasdaq">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        PayPal
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Verified
      </p>
    </div>
  );
}

function Content5() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[113px]" data-name="Content">
      <div className="relative shrink-0 size-[48px]" data-name="Company">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="white" id="Ellipse" r="23.5" stroke="#F4F4F5" />
        </svg>
        <PayPal />
      </div>
      <Nasdaq />
    </div>
  );
}

function Content4() {
  return (
    <div className="content-stretch flex items-center justify-between relative shrink-0 w-full" data-name="Content">
      <Content5 />
      <Label className="bg-[#ceefdf] relative rounded-[100px] shrink-0" />
    </div>
  );
}

function Card1() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start p-[24px] relative rounded-[16px] shrink-0" data-name="Card #2">
      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[16px]" />
      <Title1 />
      <Content4 />
    </div>
  );
}

function Component2() {
  return (
    <div className="content-stretch flex gap-[32px] items-start relative shrink-0" data-name="#">
      <Card />
      <Card1 />
    </div>
  );
}

function Content7() {
  return (
    <div className="bg-[#f4f4f5] content-stretch flex items-center justify-center p-[4px] relative rounded-[8px] shrink-0" data-name="Content">
      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[8px]" />
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0a112f] text-[14px] text-center w-[28px]">1M</p>
    </div>
  );
}

function Content8() {
  return (
    <div className="content-stretch flex items-center justify-center p-[4px] relative rounded-[8px] shrink-0" data-name="Content">
      <p className="[word-break:break-word] font-['TT_Hoves:Regular',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[14px] text-center tracking-[0.14px] w-[28px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        3M
      </p>
    </div>
  );
}

function Content9() {
  return (
    <div className="content-stretch flex items-center justify-center p-[4px] relative rounded-[8px] shrink-0" data-name="Content">
      <p className="[word-break:break-word] font-['TT_Hoves:Regular',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[14px] text-center tracking-[0.14px] w-[28px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        6M
      </p>
    </div>
  );
}

function Content10() {
  return (
    <div className="content-stretch flex items-center justify-center p-[4px] relative rounded-[8px] shrink-0" data-name="Content">
      <p className="[word-break:break-word] font-['TT_Hoves:Regular',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#70707a] text-[14px] text-center tracking-[0.14px] w-[28px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1Y
      </p>
    </div>
  );
}

function Timeframes() {
  return (
    <div className="content-stretch flex gap-[8px] items-start relative shrink-0" data-name="Timeframes">
      <Content7 />
      <Content8 />
      <Content9 />
      <Content10 />
    </div>
  );
}

function Content6() {
  return (
    <div className="content-stretch flex gap-[261px] items-start relative shrink-0" data-name="Content">
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.5] not-italic relative shrink-0 text-[#0a112f] text-[20px] whitespace-nowrap">Payment History</p>
      <Timeframes />
    </div>
  );
}

function Content11() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0" data-name="Content">
      <div className="bg-[#ceefdf] relative rounded-[100px] shrink-0" data-name="Badge">
        <div className="flex flex-row items-center justify-center overflow-clip rounded-[inherit] size-full">
          <div className="content-stretch flex items-center justify-center px-[8px] relative size-full">
            <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[1.6] not-italic relative shrink-0 text-[#0aaf60] text-[16px] tracking-[-0.32px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
              +23%
            </p>
          </div>
        </div>
      </div>
      <p className="[word-break:break-word] font-['TT_Hoves:Regular',sans-serif] leading-[1.6] not-italic opacity-50 relative shrink-0 text-[#0a112f] text-[14px] tracking-[0.14px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        vs last month
      </p>
    </div>
  );
}

function Value() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0" data-name="Value">
      <p className="[word-break:break-word] font-['TT_Hoves:Medium',sans-serif] leading-[0] not-italic relative shrink-0 text-[#0a112f] text-[0px] tracking-[-0.4px] whitespace-nowrap" style={{ fontFeatureSettings: '"ss03" 1' }}>
        <span className="leading-[1.5] text-[40px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
          $12,135
        </span>
        <span className="leading-[1.3] text-[#9096a2] text-[32px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
          .69
        </span>
      </p>
      <Content11 />
    </div>
  );
}

function Title2() {
  return (
    <div className="content-stretch flex flex-col gap-[10px] items-start relative shrink-0" data-name="Title">
      <Content6 />
      <Value />
    </div>
  );
}

function Indicator1() {
  return (
    <div className="col-1 ml-[91px] mt-[118px] relative row-1 size-[16px]" data-name="Indicator">
      <div className="absolute inset-[-37.5%_-62.5%_-87.5%_-62.5%]">
        <svg className="block size-full" fill="none" height="36" preserveAspectRatio="none" viewBox="0 0 36 36" width="36">
          <g id="Indicator">
            <g filter="url(#filter0_d_0_728)" id="Ellipse">
              <circle cx="18" cy="14" fill="white" r="8" />
            </g>
            <circle cx="18" cy="14" fill="#3981F7" id="Ellipse_2" r="3" />
          </g>
          <defs>
            <filter colorInterpolationFilters="sRGB" filterUnits="userSpaceOnUse" height="36" id="filter0_d_0_728" width="36" x="0" y="0">
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feColorMatrix in="SourceAlpha" result="hardAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" />
              <feOffset dy="4" />
              <feGaussianBlur stdDeviation="5" />
              <feColorMatrix type="matrix" values="0 0 0 0 0.301961 0 0 0 0 0.392157 0 0 0 0 1 0 0 0 0.25 0" />
              <feBlend in2="BackgroundImageFix" mode="normal" result="effect1_dropShadow_0_728" />
              <feBlend in="SourceGraphic" in2="effect1_dropShadow_0_728" mode="normal" result="shape" />
            </filter>
          </defs>
        </svg>
      </div>
    </div>
  );
}

function Base() {
  return (
    <div className="col-1 h-[114px] ml-0 mt-0 relative row-1 w-[198px]" data-name="Base">
      <svg className="absolute block inset-0 size-full" fill="none" height="114" preserveAspectRatio="none" viewBox="0 0 198 114" width="198">
        <g id="Base">
          <rect fill="white" height="108" id="Rectangle 2649" rx="8" width="198" />
          <path d={svgPaths.p253f6000} fill="white" id="Polygon 3" />
        </g>
      </svg>
    </div>
  );
}

function Text1() {
  return (
    <div className="[word-break:break-word] content-stretch flex font-['TT_Hoves:Medium',sans-serif] gap-[8px] items-center justify-center leading-[1.6] not-italic relative shrink-0 whitespace-nowrap" data-name="Text">
      <p className="relative shrink-0 text-[#70707a] text-[14px] text-center">Revenue</p>
      <p className="relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        $4,251
      </p>
    </div>
  );
}

function Frame1() {
  return (
    <div className="col-1 content-stretch flex gap-[8px] items-center ml-[8px] mt-[8px] relative row-1">
      <Icon className="relative shrink-0 size-[24px]" property1="Dollar" />
      <Text1 />
    </div>
  );
}

function DistanceDuration() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-[12px] mt-[48px] place-items-start relative row-1" data-name="Distance & Duration">
      <div className="bg-[#f3f4f7] col-1 h-[48px] ml-0 mt-0 relative rounded-[8px] row-1 w-[174px]" />
      <Frame1 />
    </div>
  );
}

function Hover() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-0 mt-0 place-items-start relative row-1" data-name="Hover">
      <Base />
      <DistanceDuration />
      <p className="[word-break:break-word] col-1 font-['TT_Hoves:Medium',sans-serif] leading-[1.6] ml-[16px] mt-[16px] not-italic relative row-1 text-[#70707a] text-[14px] whitespace-nowrap">Tuesday, Feb 15, 2022</p>
    </div>
  );
}

function Indicator() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-[213px] mt-0 place-items-start relative row-1" data-name="Indicator">
      <Indicator1 />
      <Hover />
    </div>
  );
}

function Charts() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0" data-name="Charts">
      <div className="col-1 h-[174px] ml-0 mt-[105px] relative row-1 w-[626px]">
        <svg className="absolute block inset-0 size-full" fill="none" height="174" preserveAspectRatio="none" viewBox="0 0 626 174" width="626">
          <path d={svgPaths.p7dec500} fill="url(#paint0_linear_0_735)" fillOpacity="0.2" id="Vector 40" />
          <defs>
            <linearGradient gradientUnits="userSpaceOnUse" id="paint0_linear_0_735" x1="313" x2="313" y1="-33.1429" y2="174">
              <stop stopColor="#30C559" stopOpacity="0.7" />
              <stop offset="1" stopColor="#30C559" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div className="col-1 h-[95.505px] ml-0 mt-[105px] relative row-1 w-[626px]">
        <div className="absolute inset-[-1.57%_-0.24%_-0.95%_-0.24%]">
          <svg className="block size-full" fill="none" height="97.9141" preserveAspectRatio="none" viewBox="0 0 629.001 97.9141" width="629.001">
            <path d={svgPaths.p4f73b80} id="Vector 41" stroke="#0AAF60" strokeLinecap="round" strokeWidth="3" />
          </svg>
        </div>
      </div>
      <Indicator />
    </div>
  );
}

function Timeframe() {
  return (
    <div className="[word-break:break-word] content-stretch flex gap-[96px] items-start leading-[1.6] not-italic relative shrink-0 text-[14px] whitespace-nowrap" data-name="Timeframe">
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#9096a2] text-center tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Feb 1
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#9096a2] text-center tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Feb 8
      </p>
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f]">Feb 15</p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#9096a2] text-center tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Feb 22
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#9096a2] text-center tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Feb 28
      </p>
    </div>
  );
}

function Card2() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-center py-[24px] relative rounded-[16px] shrink-0" data-name="Card #3">
      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[16px]" />
      <Title2 />
      <Charts />
      <Timeframe />
    </div>
  );
}

function Header() {
  return (
    <div className="[word-break:break-word] content-stretch flex items-center justify-between not-italic relative shrink-0 w-[390px] whitespace-nowrap" data-name="Header">
      <p className="font-['TT_Hoves:Medium',sans-serif] leading-[1.5] relative shrink-0 text-[#15191e] text-[20px]">Transaction History</p>
      <p className="font-['TT_Hoves:DemiBold',sans-serif] leading-[1.6] relative shrink-0 text-[#3981f7] text-[14px] text-right">See All</p>
    </div>
  );
}

function Name() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Cody Fisher
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Louis Vuitton
      </p>
    </div>
  );
}

function User() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage1} />
        </div>
      </div>
      <Name />
    </div>
  );
}

function Component4() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component4 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 Jun 2022
      </p>
    </div>
  );
}

function Name1() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Esther Howard
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Starbucks
      </p>
    </div>
  );
}

function User1() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage2} />
        </div>
      </div>
      <Name1 />
    </div>
  );
}

function Component5() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount1() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component5 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 May 2022
      </p>
    </div>
  );
}

function Name2() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Wade Warren
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Louis Vuitton
      </p>
    </div>
  );
}

function User2() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage3} />
        </div>
      </div>
      <Name2 />
    </div>
  );
}

function Component6() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount2() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component6 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 Apr 2022
      </p>
    </div>
  );
}

function Name3() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Brooklyn Simmons
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Sony
      </p>
    </div>
  );
}

function User3() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage4} />
        </div>
      </div>
      <Name3 />
    </div>
  );
}

function Component7() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount3() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component7 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 Mar 2022
      </p>
    </div>
  );
}

function Name4() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Ralph Edwards
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        IBM
      </p>
    </div>
  );
}

function User4() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage5} />
        </div>
      </div>
      <Name4 />
    </div>
  );
}

function Component8() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount4() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component8 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 Feb 2022
      </p>
    </div>
  );
}

function Name5() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[4px] items-start leading-[1.6] not-italic relative shrink-0 w-[148.5px] whitespace-nowrap" data-name="Name">
      <p className="font-['TT_Hoves:Medium',sans-serif] relative shrink-0 text-[#0a112f] text-[16px] tracking-[-0.32px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        Dianne Russell
      </p>
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        The Walt Disney Company
      </p>
    </div>
  );
}

function User5() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-[170px]" data-name="User">
      <div className="relative shrink-0 size-[48px]" data-name="Avatar">
        <svg className="absolute block inset-0 size-full" fill="none" height="48" preserveAspectRatio="none" viewBox="0 0 48 48" width="48">
          <circle cx="24" cy="24" fill="#EBF3FF" id="Bg" r="24" />
        </svg>
        <div className="absolute inset-[8.33%]" data-name="Image">
          <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgImage1} />
        </div>
      </div>
      <Name5 />
    </div>
  );
}

function Component9() {
  return (
    <div className="content-stretch flex font-['TT_Hoves:Medium',sans-serif] items-baseline justify-end relative shrink-0" data-name="$">
      <p className="relative shrink-0 text-[#0a112f] text-[18px] tracking-[-0.18px]">$1,546</p>
      <p className="relative shrink-0 text-[#9096a2] text-[14px]">.12</p>
    </div>
  );
}

function Amount5() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col items-end leading-[1.6] not-italic relative self-stretch shrink-0 text-right whitespace-nowrap" data-name="Amount">
      <Component9 />
      <p className="font-['TT_Hoves:Regular',sans-serif] relative shrink-0 text-[#70707a] text-[14px] tracking-[0.14px]" style={{ fontFeatureSettings: '"ss03" 1' }}>
        1 Jan 2022
      </p>
    </div>
  );
}

function Content12() {
  return (
    <div className="content-stretch flex flex-col gap-[20px] items-start relative shrink-0 w-[390px]" data-name="Content">
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User />
            <Amount />
          </div>
        </div>
      </div>
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User1 />
            <Amount1 />
          </div>
        </div>
      </div>
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User2 />
            <Amount2 />
          </div>
        </div>
      </div>
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User3 />
            <Amount3 />
          </div>
        </div>
      </div>
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User4 />
            <Amount4 />
          </div>
        </div>
      </div>
      <div className="relative shrink-0 w-full" data-name="Transaction List/Transaction List">
        <div className="flex flex-row justify-center size-full">
          <div className="content-stretch flex items-start justify-between relative size-full">
            <User5 />
            <Amount5 />
          </div>
        </div>
      </div>
    </div>
  );
}

function Card3() {
  return (
    <div className="bg-white content-stretch flex flex-col gap-[24px] items-start p-[24px] relative rounded-[16px] shrink-0" data-name="Card #4">
      <div aria-hidden className="absolute border border-[#e4e4e7] border-solid inset-0 pointer-events-none rounded-[16px]" />
      <Header />
      <Content12 />
    </div>
  );
}

function Component3() {
  return (
    <div className="content-stretch flex gap-[32px] items-start relative shrink-0" data-name="#">
      <Card2 />
      <Card3 />
    </div>
  );
}

function Component1() {
  return (
    <div className="content-stretch flex flex-col gap-[34px] items-start pb-[32px] pt-[24px] px-[32px] relative shrink-0" data-name="#">
      <Component2 />
      <Component3 />
    </div>
  );
}

function Component() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0" data-name="#">
      <Navbar className="relative shrink-0 w-[1160px]" />
      <Component1 />
    </div>
  );
}

export default function DashboardV() {
  return (
    <div className="bg-white content-stretch flex items-start relative size-full" data-name="Dashboard v1">
      <Sidebar className="bg-white h-full relative shrink-0 w-[280px]" />
      <Component />
    </div>
  );
}